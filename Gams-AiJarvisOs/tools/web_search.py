"""
tools/web_search.py — Web search tool using Google via BrowserEngine.
No API key required — uses real browser automation.
"""
from computer.browser_engine import browser_engine


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search Google and return extracted page text from the results page.
    Args:
        query: Search query string
        max_results: (unused, kept for API compatibility)
    Returns:
        Extracted text from search results page
    """
    try:
        browser_engine.search_google(query)
        text = browser_engine.extract_text()
        # Trim to first 4000 chars to avoid overwhelming the LLM
        return text[:4000] if text else "No results found."
    except Exception as e:
        return f"Search failed: {e}"


def open_and_read(url: str) -> str:
    """Open a URL and return its text content."""
    try:
        browser_engine.open(url)
        return browser_engine.extract_text()[:4000]
    except Exception as e:
        return f"Cannot read {url}: {e}"
