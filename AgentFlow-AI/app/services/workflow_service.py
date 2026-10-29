from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import ApprovalRequest, WorkflowRun, WorkflowStep
from app.workflows.engine import run_workflow


def create_workflow_run(
    db: Session,
    goal: str,
) -> WorkflowRun:
    """Create a database record before workflow execution."""
    run = WorkflowRun(
        goal=goal,
        status="pending",
        requires_approval=False,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def record_workflow_steps(
    db: Session,
    run: WorkflowRun,
    results: list[dict[str, Any]],
) -> None:
    """Persist individual step execution audit records."""
    # Remove any existing steps for idempotency during retries
    db.query(WorkflowStep).filter(WorkflowStep.run_id == run.id).delete()

    for item in results:
        step = WorkflowStep(
            run_id=run.id,
            step_id=item.get("step_id", 1),
            agent=item.get("agent", "unknown"),
            description=item.get("description", ""),
            status=item.get("status", "completed"),
            parameters=item.get("parameters"),
            result=item.get("result"),
            error_message=item.get("result", {}).get("error") if item.get("status") == "failed" else None,
            duration_seconds=item.get("duration_seconds"),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        db.add(step)
    db.commit()


def check_and_create_approval_request(
    db: Session,
    run: WorkflowRun,
    results: list[dict[str, Any]],
) -> ApprovalRequest | None:
    """Check if any step requires human approval and record approval request."""
    for item in results:
        if item.get("status") == "awaiting_approval":
            # Check if approval already created
            existing = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.run_id == run.id,
                    ApprovalRequest.step_id == item.get("step_id"),
                )
                .first()
            )
            if not existing:
                req = ApprovalRequest(
                    run_id=run.id,
                    step_id=item.get("step_id", 1),
                    action_type=item.get("agent", "protected_action"),
                    description=item.get("description", "Action requires human approval"),
                    parameters=item.get("result", {}).get("preview") or item.get("parameters"),
                    status="pending",
                )
                db.add(req)
                db.commit()
                db.refresh(req)
                return req
            return existing
    return None


def complete_workflow_run(
    db: Session,
    run: WorkflowRun,
    result: dict[str, Any],
) -> WorkflowRun:
    """Save the plan, results, and duration after execution."""
    run.goal = result.get("goal", run.goal)
    run.status = result.get("status", "completed")
    run.plan = result.get("plan", {})
    run.results = result.get("results", [])
    run.duration_seconds = result.get("duration_seconds")
    run.error_message = None if run.status != "failed" else result.get("message")

    if run.status == "completed" or run.status == "failed":
        run.completed_at = datetime.now(timezone.utc)

    # Check requires_approval flag
    requires_approval = bool(run.plan.get("requires_approval", False)) or (run.status == "awaiting_approval")
    run.requires_approval = requires_approval

    db.commit()
    db.refresh(run)

    # Record step rows
    record_workflow_steps(db, run, run.results or [])

    # If awaiting approval, create approval request record
    if run.status == "awaiting_approval":
        check_and_create_approval_request(db, run, run.results or [])

    return run


def fail_workflow_run(
    db: Session,
    run: WorkflowRun,
    error_message: str,
) -> WorkflowRun:
    """Record a workflow failure."""
    run.status = "failed"
    run.error_message = error_message
    run.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)
    return run


def get_workflow_run(
    db: Session,
    run_id: int,
) -> WorkflowRun | None:
    """Retrieve one workflow execution by ID."""
    return db.get(WorkflowRun, run_id)


def list_workflow_runs(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    search: str | None = None,
) -> list[WorkflowRun]:
    """Return workflow executions with optional status and search filtering."""
    query = db.query(WorkflowRun)

    if status and status.strip():
        query = query.filter(WorkflowRun.status == status.strip())

    if search and search.strip():
        query = query.filter(WorkflowRun.goal.ilike(f"%{search.strip()}%"))

    safe_limit = max(1, min(limit, 100))
    return (
        query.order_by(WorkflowRun.id.desc())
        .offset(offset)
        .limit(safe_limit)
        .all()
    )


def cancel_workflow_run(
    db: Session,
    run_id: int,
) -> WorkflowRun | None:
    """Cancel an active or awaiting approval workflow."""
    run = db.get(WorkflowRun, run_id)
    if not run:
        return None

    if run.status in ("completed", "cancelled"):
        return run

    run.status = "cancelled"
    run.error_message = "Workflow was cancelled by user request."
    run.completed_at = datetime.now(timezone.utc)

    # Mark any pending approvals as rejected/cancelled
    pending_approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.run_id == run_id, ApprovalRequest.status == "pending")
        .all()
    )
    for app_req in pending_approvals:
        app_req.status = "rejected"
        app_req.decided_at = datetime.now(timezone.utc)
        app_req.decision_notes = "Workflow cancelled."

    db.commit()
    db.refresh(run)
    return run


def list_pending_approvals(db: Session) -> list[ApprovalRequest]:
    """Retrieve all pending approval requests."""
    return (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.id.desc())
        .all()
    )


def approve_action(
    db: Session,
    approval_id: int,
    notes: str = "",
) -> tuple[ApprovalRequest | None, WorkflowRun | None]:
    """Approve a protected operation and resume workflow execution."""
    approval = db.get(ApprovalRequest, approval_id)
    if not approval or approval.status != "pending":
        return approval, None

    approval.status = "approved"
    approval.decided_at = datetime.now(timezone.utc)
    approval.decision_notes = notes or "Approved by operator."

    run = db.get(WorkflowRun, approval.run_id)
    if not run:
        db.commit()
        return approval, None

    # Resume the workflow execution with approved step
    plan = run.plan or {}
    steps = plan.get("steps", [])
    step_index = 0
    for idx, s in enumerate(steps):
        if s.get("step_id") == approval.step_id:
            step_index = idx
            break

    # Prior results up to this step
    prior_results = [r for r in (run.results or []) if r.get("step_id") != approval.step_id]

    resume_result = run_workflow(
        user_goal=run.goal,
        pre_plan=plan,
        approved_step_id=approval.step_id,
        current_results=prior_results,
        start_step_index=step_index,
    )

    complete_workflow_run(db, run, resume_result)
    db.commit()
    db.refresh(approval)
    db.refresh(run)

    return approval, run


def reject_action(
    db: Session,
    approval_id: int,
    notes: str = "",
) -> tuple[ApprovalRequest | None, WorkflowRun | None]:
    """Reject a protected operation and mark workflow cancelled."""
    approval = db.get(ApprovalRequest, approval_id)
    if not approval or approval.status != "pending":
        return approval, None

    approval.status = "rejected"
    approval.decided_at = datetime.now(timezone.utc)
    approval.decision_notes = notes or "Rejected by operator."

    run = db.get(WorkflowRun, approval.run_id)
    if run:
        run.status = "cancelled"
        run.error_message = f"Action in Step {approval.step_id} rejected by user. {notes}".strip()
        run.completed_at = datetime.now(timezone.utc)
        # Update matching step status in results
        updated_results = []
        for r in (run.results or []):
            if r.get("step_id") == approval.step_id:
                r["status"] = "rejected"
                r["result"] = {"rejection_reason": approval.decision_notes}
            updated_results.append(r)
        run.results = updated_results
        record_workflow_steps(db, run, updated_results)

    db.commit()
    db.refresh(approval)
    if run:
        db.refresh(run)

    return approval, run


def get_analytics_summary(db: Session) -> dict[str, Any]:
    """Calculate real platform analytics directly from the SQLite database."""
    total = db.query(WorkflowRun).count()
    completed = db.query(WorkflowRun).filter(WorkflowRun.status == "completed").count()
    failed = db.query(WorkflowRun).filter(WorkflowRun.status == "failed").count()
    awaiting = db.query(WorkflowRun).filter(WorkflowRun.status == "awaiting_approval").count()
    running = db.query(WorkflowRun).filter(WorkflowRun.status.in_(["running", "pending", "planned"])).count()

    success_rate = round((completed / max(1, completed + failed)) * 100, 1)

    # Average duration
    durations = [
        r.duration_seconds
        for r in db.query(WorkflowRun.duration_seconds).filter(WorkflowRun.duration_seconds.isnot(None)).all()
        if r[0] is not None
    ]
    avg_duration = round(sum(durations) / max(1, len(durations)), 2) if durations else 0.0

    # Agent execution counts from workflow_steps
    agent_counts = (
        db.query(WorkflowStep.agent, func.count(WorkflowStep.id))
        .group_by(WorkflowStep.agent)
        .all()
    )
    agent_usage = [{"agent": row[0], "count": int(row[1])} for row in agent_counts]

    # Daily volume for last 7 days
    runs = db.query(WorkflowRun).order_by(WorkflowRun.created_at.asc()).all()
    daily_map: dict[str, dict[str, int]] = {}
    for r in runs:
        if r.created_at:
            day_str = r.created_at.strftime("%Y-%m-%d")
            if day_str not in daily_map:
                daily_map[day_str] = {"count": 0, "completed": 0, "failed": 0}
            daily_map[day_str]["count"] += 1
            if r.status == "completed":
                daily_map[day_str]["completed"] += 1
            elif r.status == "failed":
                daily_map[day_str]["failed"] += 1

    daily_volume = [
        {
            "date": day,
            "count": stats["count"],
            "completed": stats["completed"],
            "failed": stats["failed"],
        }
        for day, stats in daily_map.items()
    ]

    return {
        "total_workflows": total,
        "completed": completed,
        "failed": failed,
        "awaiting_approval": awaiting,
        "running": running,
        "success_rate_percent": success_rate,
        "avg_duration_seconds": avg_duration,
        "agent_usage": agent_usage,
        "daily_volume": daily_volume,
    }
