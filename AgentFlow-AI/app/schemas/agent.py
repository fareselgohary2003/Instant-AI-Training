from typing import Any
from pydantic import BaseModel


class AgentInfoResponse(BaseModel):
    id: str
    name: str
    description: str
    capabilities: list[str]
    tools: list[str]
    requires_approval: bool
    is_enabled: bool
    disabled_reason: str | None = None
