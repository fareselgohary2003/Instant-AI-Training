from typing import Any
from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The task or goal the user wants the AI agents to complete.",
    )


class WorkflowStepResult(BaseModel):
    step_id: int
    agent: str
    description: str
    status: str
    parameters: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    duration_seconds: float | None = None


class WorkflowRunResponse(BaseModel):
    run_id: int
    goal: str
    status: str
    plan: dict[str, Any]
    results: list[WorkflowStepResult]
    duration_seconds: float | None = None
    message: str
    created_at: str | None = None
    completed_at: str | None = None


class WorkflowListItem(BaseModel):
    run_id: int
    goal: str
    status: str
    step_count: int = 0
    duration_seconds: float | None = None
    created_at: str | None = None
    completed_at: str | None = None


class WorkflowHistoryResponse(BaseModel):
    count: int
    items: list[WorkflowRunResponse]


class WorkflowCancelResponse(BaseModel):
    run_id: int
    status: str
    message: str
