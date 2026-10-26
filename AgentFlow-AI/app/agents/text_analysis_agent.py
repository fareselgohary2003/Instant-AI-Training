from typing import Any
from app.tools.text_analysis_tool import analyze_text


def run_text_analysis_agent(parameters: dict[str, Any]) -> dict[str, Any]:
    """Execute the text analysis agent with validated parameters."""
    text = parameters.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("The text analysis agent requires a valid 'text' parameter.")

    include_summary = bool(parameters.get("include_summary", False))
    return analyze_text(text.strip(), include_llm_summary=include_summary)
