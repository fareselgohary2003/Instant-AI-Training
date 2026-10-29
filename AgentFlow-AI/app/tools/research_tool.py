import os
from datetime import datetime, timezone
from typing import Any
import httpx


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """Execute a web search using Tavily API if configured, or DuckDuckGo fallback.

    Returns structured results with source URLs, titles, snippets, and retrieval timestamp.
    """
    clean_query = (query or "").strip()
    if not clean_query:
        raise ValueError("Search query cannot be empty.")

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    retrieved_at = datetime.now(timezone.utc).isoformat()

    # Strategy 1: Use Tavily API if key is present
    if tavily_key:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": clean_query,
                        "search_depth": "basic",
                        "max_results": min(max_results, 5),
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    results = [
                        {
                            "title": item.get("title", "No title"),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "retrieved_at": retrieved_at,
                        }
                        for item in data.get("results", [])
                    ]
                    return {
                        "provider": "Tavily",
                        "query": clean_query,
                        "result_count": len(results),
                        "results": results,
                        "status": "success",
                        "note": "Web sources retrieved via Tavily Search API.",
                    }
        except Exception as exc:
            pass  # Fall through to fallback or clear explanation

    # Strategy 2: Safe public search fallback via DuckDuckGo Instant Answer API
    try:
        with httpx.Client(timeout=10.0, headers={"User-Agent": "AITaskAgent/1.0"}) as client:
            resp = client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": clean_query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                abstract = data.get("AbstractText")
                abstract_url = data.get("AbstractURL")
                heading = data.get("Heading")
                if abstract and abstract_url:
                    results.append({
                        "title": heading or clean_query,
                        "url": abstract_url,
                        "snippet": abstract,
                        "retrieved_at": retrieved_at,
                    })

                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                        results.append({
                            "title": topic.get("Text")[:60] + "...",
                            "url": topic.get("FirstURL"),
                            "snippet": topic.get("Text"),
                            "retrieved_at": retrieved_at,
                        })

                if results:
                    return {
                        "provider": "DuckDuckGo Instant Answer",
                        "query": clean_query,
                        "result_count": len(results),
                        "results": results,
                        "status": "success",
                        "note": "Verified sources retrieved via DuckDuckGo API.",
                    }
    except Exception:
        pass

    # If neither returned live results
    return {
        "provider": "None",
        "query": clean_query,
        "result_count": 0,
        "results": [],
        "status": "unconfigured_or_unavailable",
        "note": (
            "Web search provider (Tavily) is not configured or external service was unavailable. "
            "To enable live web search, add TAVILY_API_KEY to your .env file."
        ),
    }
