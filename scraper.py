"""Web scraping module — Firecrawl primary, httpx/bs4 fallback."""

from __future__ import annotations

import os

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

_firecrawl_app = None


def _get_firecrawl():
    global _firecrawl_app
    if _firecrawl_app is None:
        api_key = os.getenv("FIRECRAWL_API_KEY", "")
        if not api_key:
            return None
        from firecrawl import FirecrawlApp

        _firecrawl_app = FirecrawlApp(api_key=api_key)
    return _firecrawl_app


async def scrape(url: str) -> str:
    """Scrape a URL and return clean markdown content."""
    fc = _get_firecrawl()
    if fc:
        result = fc.scrape_url(url, formats=["markdown"])
        return result.get("markdown", "") if isinstance(result, dict) else result.markdown

    # Fallback: httpx + bs4 + markdownify
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return markdownify(str(soup.body or soup), strip=["img"])


async def search(query: str, limit: int = 3) -> list[dict]:
    """Search the web and return scraped results.

    Returns list of {"title": ..., "url": ..., "content": ...}.
    """
    fc = _get_firecrawl()
    if fc:
        results = fc.search(query, limit=limit)
        items = results if isinstance(results, list) else results.data
        return [
            {
                "title": r.get("title", "") if isinstance(r, dict) else r.title,
                "url": r.get("url", "") if isinstance(r, dict) else r.url,
                "content": (
                    r.get("markdown", r.get("content", ""))
                    if isinstance(r, dict)
                    else r.markdown
                ),
            }
            for r in items[:limit]
        ]

    # Fallback: no search without Firecrawl — return empty
    return []
