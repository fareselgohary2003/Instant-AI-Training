import json
import re
from typing import Any

from app.agent.llm import get_llm_response
from app.agents.registry import AGENT_REGISTRY

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent of an enterprise multi-agent workflow platform.
Your job is to decompose the user's natural language goal into a structured, executable multi-agent plan.

Available Agents:
- weather_agent: Retrieve current weather & forecasts for a city. (Parameters: {"city": "string"})
- text_analysis_agent: Analyze text for word count, keywords, length, sentiment. (Parameters: {"text": "string"})
- research_agent: Search the web for up-to-date facts and sources. (Parameters: {"query": "string"})
- general_agent: Answer general questions, explain plans, or draft text. (Parameters: {"query": "string"})
- data_analysis_agent: Parse tabular CSV data, metrics and distributions. (Parameters: {"csv_content": "string"})
- email_agent: Prepare an email to send. SENSITIVE: Sending email requires human approval. (Parameters: {"recipient": "email", "subject": "string", "body": "string"})

You MUST return ONLY a valid JSON object matching this schema:
{
  "goal": "Concise summary of the user's objective",
  "interpretation": "Short technical interpretation of how the agents will accomplish the goal",
  "steps": [
    {
      "step_id": 1,
      "agent": "weather_agent",
      "description": "Specific action to perform",
      "parameters": {"city": "Cairo"},
      "depends_on": []
    }
  ],
  "requires_approval": false
}

Rules:
1. ONLY use agents from the list above. Never use code_execution_agent or unlisted agents.
2. Step IDs must be sequential integers starting from 1.
3. Every step MUST have an 'agent', 'description', and 'parameters' object.
4. If a step depends on an earlier step's output, list that step_id in 'depends_on'.
5. Set 'requires_approval' to TRUE if ANY step uses 'email_agent' or modifies external state.
6. Never invent missing critical parameters (like random fake email addresses). If the user didn't provide a recipient for an email, use 'recipient@example.com' or leave it to be validated.
7. Return raw JSON only with NO markdown fences, NO preamble, and NO extra text.
"""


def _clean_json_text(text: str) -> str:
    """Strip markdown code blocks or wrapping quotes from LLM output."""
    cleaned = text.strip()
    # Strip markdown ```json ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def validate_plan_structure(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate a parsed plan dictionary against strict agent registry and parameter schemas."""
    if not isinstance(plan, dict):
        raise ValueError("Plan must be a JSON object.")

    goal = plan.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        plan["goal"] = "Workflow Execution Plan"

    steps = plan.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Plan must contain a 'steps' list.")

    requires_approval = False

    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"Step at index {index} must be a JSON object.")

        step_id = step.get("step_id")
        if step_id != index:
            step["step_id"] = index

        agent = step.get("agent")
        if not agent or agent not in AGENT_REGISTRY:
            raise ValueError(f"Step {index} references unknown agent: '{agent}'")

        agent_def = AGENT_REGISTRY[agent]
        if not agent_def.is_enabled:
            reason = agent_def.disabled_reason or "Agent is currently disabled."
            raise ValueError(f"Agent '{agent}' cannot be scheduled: {reason}")

        if not isinstance(step.get("parameters"), dict):
            step["parameters"] = {}

        if not isinstance(step.get("description"), str) or not step["description"].strip():
            step["description"] = f"Execute step {index} via {agent_def.name}"

        # If agent requires approval, flag workflow
        if agent_def.requires_approval or agent == "email_agent":
            requires_approval = True

        if "depends_on" not in step or not isinstance(step.get("depends_on"), list):
            step["depends_on"] = []

    plan["requires_approval"] = requires_approval or bool(plan.get("requires_approval", False))
    return plan


def create_deterministic_fallback_plan(goal: str) -> dict[str, Any]:
    """Create a deterministic fallback plan if LLM is unavailable or unconfigured."""
    lower_goal = goal.lower()
    steps = []

    # Check for weather intent
    if any(k in lower_goal for k in ["weather", "temperature", "forecast", "climate"]):
        # Extract potential city
        city_match = re.search(r"in\s+([A-Za-z\s]+?)(?:\s+and|\s+for|\.|$)", goal, re.IGNORECASE)
        city = city_match.group(1).strip() if city_match else "Cairo"
        steps.append({
            "step_id": len(steps) + 1,
            "agent": "weather_agent",
            "description": f"Retrieve current weather conditions for {city}.",
            "parameters": {"city": city},
            "depends_on": [],
        })

    # Check for text analysis intent
    if any(k in lower_goal for k in ["analyze", "word count", "sentiment", "text"]):
        text_match = re.search(r'["\'](.*?)["\']', goal)
        text_to_analyze = text_match.group(1) if text_match else goal
        steps.append({
            "step_id": len(steps) + 1,
            "agent": "text_analysis_agent",
            "description": "Perform text and sentiment analysis on provided content.",
            "parameters": {"text": text_to_analyze},
            "depends_on": [],
        })

    # Check for search/research intent
    if any(k in lower_goal for k in ["search", "research", "find information", "who is", "what is"]):
        steps.append({
            "step_id": len(steps) + 1,
            "agent": "research_agent",
            "description": f"Search the web for information regarding: {goal[:60]}",
            "parameters": {"query": goal},
            "depends_on": [],
        })

    # Check for email intent
    if any(k in lower_goal for k in ["email", "send an email", "mail"]):
        steps.append({
            "step_id": len(steps) + 1,
            "agent": "email_agent",
            "description": "Prepare and preview email notification.",
            "parameters": {
                "recipient": "user@example.com",
                "subject": f"Update regarding: {goal[:40]}",
                "body": f"Workflow execution report for goal: {goal}",
            },
            "depends_on": [],
        })

    if not steps:
        steps.append({
            "step_id": 1,
            "agent": "general_agent",
            "description": "Analyze and respond to user query.",
            "parameters": {"query": goal},
            "depends_on": [],
        })

    requires_approval = any(s["agent"] == "email_agent" for s in steps)
    return {
        "goal": goal,
        "interpretation": "Deterministic fallback plan constructed based on recognized intents.",
        "steps": steps,
        "requires_approval": requires_approval,
    }


def create_plan(user_goal: str) -> dict[str, Any]:
    """Generate and validate an execution plan for a user goal."""
    if not isinstance(user_goal, str) or not user_goal.strip():
        raise ValueError("User goal cannot be empty.")

    cleaned_goal = user_goal.strip()

    try:
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
            {"role": "user", "content": cleaned_goal},
        ]
        raw_response = get_llm_response(messages)
        cleaned_response = _clean_json_text(raw_response)
        parsed_plan = json.loads(cleaned_response)
        return validate_plan_structure(parsed_plan)
    except Exception as exc:
        # Fallback to deterministic plan generation if LLM is unavailable or returns non-JSON
        fallback = create_deterministic_fallback_plan(cleaned_goal)
        fallback["interpretation"] = (
            f"Deterministic plan formed (LLM note: {str(exc)[:120] if str(exc) else 'Deterministic routing applied'})."
        )
        return validate_plan_structure(fallback)
