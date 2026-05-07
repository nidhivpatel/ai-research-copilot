"""Web scraping module — Firecrawl primary, httpx/bs4 fallback."""

from __future__ import annotations

import asyncio
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
        result = fc.scrape(url, formats=["markdown"])
        return result.markdown or ""

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
        items = results.web or []
        # Scrape all URLs in parallel for speed
        async def _scrape_item(r):
            content = await scrape(r.url)
            return {"title": r.title or "", "url": r.url, "content": content}
        return await asyncio.gather(*[_scrape_item(r) for r in items[:limit]])

    # Fallback: no search without Firecrawl — return empty
    return []
