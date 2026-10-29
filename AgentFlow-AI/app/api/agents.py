from fastapi import APIRouter
from app.agents.registry import list_registered_agents
from app.schemas.agent import AgentInfoResponse

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("", response_model=list[AgentInfoResponse], summary="List all registered agents and capabilities")
def get_agents() -> list[dict]:
    return list_registered_agents()
