from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ApprovalRequest
from app.schemas.approval import ApprovalDecisionRequest, ApprovalResponse
from app.schemas.workflow import WorkflowRunResponse
from app.services.workflow_service import approve_action, list_pending_approvals, reject_action

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


def serialize_approval(approval: ApprovalRequest) -> dict[str, Any]:
    return {
        "id": approval.id,
        "run_id": approval.run_id,
        "step_id": approval.step_id,
        "action_type": approval.action_type,
        "description": approval.description,
        "parameters": approval.parameters or {},
        "status": approval.status,
        "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
        "decision_notes": approval.decision_notes,
    }


@router.get("", response_model=list[ApprovalResponse], summary="List pending approvals")
def get_approvals(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    approvals = list_pending_approvals(db)
    return [serialize_approval(a) for a in approvals]


@router.post("/{approval_id}/approve", summary="Approve a protected operation")
def approve_pending_action(
    approval_id: int,
    decision: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    approval, run = approve_action(db, approval_id, notes=decision.notes)
    if not approval:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request {approval_id} not found or already decided.",
        )

    return {
        "success": True,
        "approval": serialize_approval(approval),
        "run_id": run.id if run else approval.run_id,
        "workflow_status": run.status if run else "resumed",
        "message": "Protected action approved and workflow resumed.",
    }


@router.post("/{approval_id}/reject", summary="Reject a protected operation")
def reject_pending_action(
    approval_id: int,
    decision: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    approval, run = reject_action(db, approval_id, notes=decision.notes)
    if not approval:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request {approval_id} not found or already decided.",
        )

    return {
        "success": True,
        "approval": serialize_approval(approval),
        "run_id": run.id if run else approval.run_id,
        "workflow_status": run.status if run else "cancelled",
        "message": "Protected action rejected.",
    }
