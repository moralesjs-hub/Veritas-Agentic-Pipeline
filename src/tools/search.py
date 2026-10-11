from typing import List

def run_web_search(query: str, max_results: int = 2) -> List[str]:
    """Retrieves search snippets with a strict fallback to prevent deadlocks."""
    results = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        ddgs = DDGS(timeout=10)
        raw_results = list(ddgs.text(query, max_results=max_results))
        for res in raw_results:
            title = res.get("title", "")
            href = res.get("href", "")
            body = res.get("body", "")
            results.append(f"Title: {title}\nSource: {href}\nContent: {body}")
    except Exception as e:
        results.append(f"Search fallback note: Could not retrieve live results for '{query}' ({e}). Rely on core literature context.")
    return results