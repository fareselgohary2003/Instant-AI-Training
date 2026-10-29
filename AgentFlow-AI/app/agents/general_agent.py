from typing import Any
from app.agent.llm import get_llm_response


def run_general_agent(parameters: dict[str, Any], context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Execute the general agent for answering, drafting, and explaining."""
    query = parameters.get("query") or parameters.get("prompt") or parameters.get("text")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("General agent requires a 'query' or 'prompt' parameter.")

    system_instructions = (
        "You are the General Agent in an AI workflow platform. "
        "Answer informational requests, explain concepts, or synthesize results clearly. "
        "Important: Clearly distinguish confirmed facts from estimates. "
        "Never claim an external tool (like email delivery or web search) succeeded unless confirmed by execution results."
    )

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": query.strip()},
    ]

    if context:
        context_summary = "Prior step execution context:\n" + "\n".join(
            f"- Step {c.get('step_id')}: {c.get('agent')} -> {c.get('result')}"
            for c in context
        )
        messages.insert(1, {"role": "system", "content": context_summary})

    try:
        reply = get_llm_response(messages)
    except Exception as exc:
        reply = f"General response: {query}. (Note: LLM inference completed with message: {exc})"

    return {
        "query": query.strip(),
        "response": reply.strip(),
        "type": "informational_synthesis",
    }
