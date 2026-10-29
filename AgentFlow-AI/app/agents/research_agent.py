from typing import Any
from app.tools.research_tool import search_web


def run_research_agent(parameters: dict[str, Any]) -> dict[str, Any]:
    """Execute research agent with web search tool."""
    query = parameters.get("query") or parameters.get("topic") or parameters.get("search_query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Research agent requires a valid 'query' parameter.")

    max_results = int(parameters.get("max_results", 5))
    search_data = search_web(query.strip(), max_results=max_results)

    return {
        "query": query.strip(),
        "provider": search_data.get("provider"),
        "result_count": search_data.get("result_count", 0),
        "sources": search_data.get("results", []),
        "status": search_data.get("status"),
        "note": search_data.get("note"),
    }
