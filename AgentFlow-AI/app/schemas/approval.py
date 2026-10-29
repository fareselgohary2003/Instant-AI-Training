from typing import Any
from pydantic import BaseModel, Field


class ApprovalResponse(BaseModel):
    id: int
    run_id: int
    step_id: int
    action_type: str
    description: str
    parameters: dict[str, Any] | None = None
    status: str
    requested_at: str | None = None
    decided_at: str | None = None
    decision_notes: str | None = None


class ApprovalDecisionRequest(BaseModel):
    notes: str = Field(
        default="",
        max_length=500,
        description="Optional justification or notes for the approval or rejection decision.",
    )
