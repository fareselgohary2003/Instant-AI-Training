from typing import Any, Callable
from pydantic import BaseModel


class AgentDefinition(BaseModel):
    id: str
    name: str
    description: str
    capabilities: list[str]
    tools: list[str]
    requires_approval: bool = False
    is_enabled: bool = True
    disabled_reason: str | None = None


# Central registry of available agent types and their operational parameters
AGENT_REGISTRY: dict[str, AgentDefinition] = {
    "supervisor": AgentDefinition(
        id="supervisor",
        name="Supervisor Agent",
        description="Analyzes user goals, breaks them into sequential or dependency-aware tasks, and coordinates execution.",
        capabilities=[
            "Goal decomposition",
            "Agent routing",
            "Dependency management",
            "Approval checkpoint detection",
        ],
        tools=["create_plan", "validate_plan"],
        requires_approval=False,
        is_enabled=True,
    ),
    "weather_agent": AgentDefinition(
        id="weather_agent",
        name="Weather Agent",
        description="Fetches live meteorological conditions and forecasts for cities worldwide using the Open-Meteo API.",
        capabilities=[
            "Current temperature & feels-like",
            "Weather conditions & humidity",
            "Wind speed & direction",
            "Geocoding coordinates resolution",
        ],
        tools=["get_weather"],
        requires_approval=False,
        is_enabled=True,
    ),
    "text_analysis_agent": AgentDefinition(
        id="text_analysis_agent",
        name="Text Analysis Agent",
        description="Performs deterministic linguistic inspection, statistical metrics, keyword extraction, and sentiment scoring.",
        capabilities=[
            "Word, character & sentence counts",
            "Average word length metrics",
            "Deterministic keyword extraction",
            "Lexicon polarity & sentiment classification",
            "Executive summarization",
        ],
        tools=["analyze_text"],
        requires_approval=False,
        is_enabled=True,
    ),
    "general_agent": AgentDefinition(
        id="general_agent",
        name="General Agent",
        description="Provides general-purpose intelligence, answers informational queries, drafts content, and synthesizes outputs.",
        capabilities=[
            "Question answering",
            "Text drafting & explanation",
            "Cross-step result synthesis",
            "Structured response generation",
        ],
        tools=["synthesize_response"],
        requires_approval=False,
        is_enabled=True,
    ),
    "email_agent": AgentDefinition(
        id="email_agent",
        name="Email Agent",
        description="Prepares, validates, and transmits emails via SMTP. All sending actions require explicit human-in-the-loop approval.",
        capabilities=[
            "Recipient validation & normalization",
            "Subject and body preview generation",
            "Protected side-effect execution via SMTP",
            "Human approval requirement enforcement",
        ],
        tools=["preview_email", "send_email"],
        requires_approval=True,
        is_enabled=True,
    ),
    "research_agent": AgentDefinition(
        id="research_agent",
        name="Research Agent",
        description="Searches the web for up-to-date facts, retrieving sourced titles, snippets, and verified source citations.",
        capabilities=[
            "Web information search",
            "Source attribution & URL verification",
            "Tavily API integration",
            "DuckDuckGo fallback search",
        ],
        tools=["search_web"],
        requires_approval=False,
        is_enabled=True,
    ),
    "data_analysis_agent": AgentDefinition(
        id="data_analysis_agent",
        name="Data Analysis Agent",
        description="Parses and analyzes tabular CSV datasets, calculating summary statistics, distributions, and chart-ready metrics.",
        capabilities=[
            "Schema inspection & missing value checks",
            "Descriptive statistics (mean, median, std, min, max)",
            "Categorical value distribution",
            "Chart-ready dataset formatting",
        ],
        tools=["analyze_tabular_data"],
        requires_approval=False,
        is_enabled=True,
    ),
    "code_execution_agent": AgentDefinition(
        id="code_execution_agent",
        name="Code Execution Agent",
        description="Isolated container environment for sandboxed code execution.",
        capabilities=[
            "Python script execution",
            "Resource-limited sandboxing",
        ],
        tools=["execute_code"],
        requires_approval=True,
        is_enabled=False,
        disabled_reason="Container sandbox (Docker/gVisor) is disabled by policy to protect the host environment.",
    ),
}


def get_agent_definition(agent_id: str) -> AgentDefinition | None:
    """Retrieve an agent specification by its unique identifier."""
    return AGENT_REGISTRY.get(agent_id)


def list_registered_agents() -> list[dict[str, Any]]:
    """Return all registered agents with their metadata and availability."""
    return [agent.model_dump() for agent in AGENT_REGISTRY.values()]
