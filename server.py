"""AI Research Copilot — MCP server exposing 4 tools."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from mcp.server.fastmcp import FastMCP

import llm_client
import scraper

mcp = FastMCP(
    "AI Research Copilot",
    instructions=(
        "An AI-powered research assistant. Use research_topic for broad research, "
        "scrape_url to read a specific page, summarize_text to condense content, "
        "and ask_llm for direct questions."
    ),
)


@mcp.tool()
async def research_topic(topic: str, depth: int = 2) -> str:
    """Search the web for a topic, scrape top results, and synthesize a research summary.

    Args:
        topic: The research topic or question to investigate.
        depth: Number of search results to scrape and analyse (default 3).
    """
    # 1. Search for relevant pages
    results = await scraper.search(topic, limit=depth)
    if not results:
        return (
            "No search results found. "
            "Set FIRECRAWL_API_KEY in .env to enable web search, "
            "or use scrape_url with a direct URL instead."
        )

    # 2. Build combined context from scraped content
    sections: list[str] = []
    for r in results:
        content = r["content"]
        if not content:
            content = await scraper.scrape(r["url"])
        sections.append(f"## {r['title']}\nSource: {r['url']}\n\n{content[:4000]}")

    combined = "\n\n---\n\n".join(sections)

    # 3. Synthesize with LLM
    instruction = (
        f"You are a research analyst. Based on the following sources about '{topic}', "
        "write a structured research summary with: "
        "1) Key Findings, 2) Important Details, 3) Sources. "
        "Be concise but thorough."
    )
    summary = llm_client.summarize(combined, instruction=instruction)

    return summary


@mcp.tool()
async def scrape_url(url: str) -> str:
    """Scrape a URL and return its content as clean markdown.

    Args:
        url: The web page URL to scrape.
    """
    content = await scraper.scrape(url)
    if not content:
        return f"Could not extract content from {url}"
    # Truncate very long pages to stay within reasonable limits
    if len(content) > 15000:
        content = content[:15000] + "\n\n... [truncated]"
    return content


@mcp.tool()
async def summarize_text(text: str, focus: str = "") -> str:
    """Summarize text using the configured LLM.

    Args:
        text: The text content to summarize.
        focus: Optional focus area to guide the summary (e.g. "security implications").
    """
    instruction = ""
    if focus:
        instruction = (
            f"Summarize the following content with a focus on: {focus}. "
            "Highlight key points and actionable insights."
        )
    return llm_client.summarize(text, instruction=instruction)


@mcp.tool()
async def ask_llm(question: str, context: str = "") -> str:
    """Ask the LLM a direct question, optionally with context.

    Args:
        question: The question to ask.
        context: Optional context or background information to include.
    """
    messages: list[dict] = []
    if context:
        messages.append(
            {
                "role": "system",
                "content": f"Use the following context to answer the user's question:\n\n{context[:8000]}",
            }
        )
    messages.append({"role": "user", "content": question})
    return llm_client.chat(messages)


if __name__ == "__main__":
    mcp.run()
