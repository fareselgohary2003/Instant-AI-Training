from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import WorkflowRun
from app.schemas.workflow import (
    WorkflowCancelResponse,
    WorkflowHistoryResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from app.services.workflow_service import (
    cancel_workflow_run,
    complete_workflow_run,
    create_workflow_run,
    fail_workflow_run,
    get_workflow_run,
    list_workflow_runs,
)
from app.workflows.engine import run_workflow

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


def serialize_workflow_run(run: WorkflowRun) -> dict[str, Any]:
    """Convert a database workflow record into an API response."""
    return {
        "run_id": run.id,
        "goal": run.goal,
        "status": run.status,
        "plan": run.plan or {},
        "results": run.results or [],
        "duration_seconds": run.duration_seconds,
        "message": run.error_message or (
            "Workflow finished."
            if run.status == "completed"
            else f"Workflow is {run.status}."
        ),
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.post(
    "/run",
    response_model=WorkflowRunResponse,
    summary="Run an AI agent workflow",
)
def run_agent_workflow(
    request: WorkflowRunRequest,
    db: Session = Depends(get_db),
) -> WorkflowRunResponse:
    goal = request.goal.strip()

    if not goal:
        raise HTTPException(
            status_code=422,
            detail="The goal must not be empty.",
        )

    run = create_workflow_run(db, goal)

    try:
        result = run_workflow(goal)
        saved_run = complete_workflow_run(db, run, result)

        response_data = serialize_workflow_run(saved_run)
        return WorkflowRunResponse(**response_data)

    except Exception as exc:
        db.rollback()
        try:
            fail_workflow_run(db, run, str(exc))
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"The workflow failed: {exc}",
        ) from exc


@router.get(
    "/history",
    summary="List previous workflow runs",
)
def workflow_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return recent workflow executions from the database with filtering."""
    runs = list_workflow_runs(db, limit=limit, offset=offset, status=status, search=search)

    return {
        "count": len(runs),
        "items": [serialize_workflow_run(run) for run in runs],
    }


@router.get(
    "/history/{run_id}",
    summary="Get one workflow run",
)
def workflow_history_detail(
    run_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the saved details of a specific workflow execution."""
    run = get_workflow_run(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow run {run_id} was not found.",
        )

    return serialize_workflow_run(run)


@router.post(
    "/{run_id}/cancel",
    response_model=WorkflowCancelResponse,
    summary="Cancel a workflow run",
)
def cancel_workflow(
    run_id: int,
    db: Session = Depends(get_db),
) -> WorkflowCancelResponse:
    """Cancel an active or awaiting approval workflow."""
    run = cancel_workflow_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Workflow run {run_id} not found.")

    return WorkflowCancelResponse(
        run_id=run.id,
        status=run.status,
        message="Workflow execution cancelled successfully.",
    )


@router.post(
    "/{run_id}/retry",
    response_model=WorkflowRunResponse,
    summary="Retry a failed workflow run",
)
def retry_workflow(
    run_id: int,
    db: Session = Depends(get_db),
) -> WorkflowRunResponse:
    """Retry execution of a previously failed workflow."""
    run = get_workflow_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Workflow run {run_id} not found.")

    if run.status != "failed" and run.status != "cancelled":
        raise HTTPException(
            status_code=400,
            detail=f"Only failed or cancelled workflows can be retried. Current status is '{run.status}'.",
        )

    run.status = "running"
    run.error_message = None
    db.commit()

    try:
        result = run_workflow(run.goal, pre_plan=run.plan)
        saved_run = complete_workflow_run(db, run, result)
        return WorkflowRunResponse(**serialize_workflow_run(saved_run))
    except Exception as exc:
        fail_workflow_run(db, run, str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Workflow retry failed: {exc}",
        ) from exc
