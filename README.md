# AI Research Copilot

An MCP server that combines **Firecrawl** (web scraping), **Langfuse** (observability), and **vLLM on Scaleway** (LLM inference) into a research assistant usable from Claude Desktop.

## Architecture

```
┌─────────────────┐     stdio      ┌──────────────────────┐
│  Claude Desktop  │◄──────────────►│   MCP Server (Python) │
│  (ENGAGE)        │                │                      │
└─────────────────┘                │  Tools:              │
                                   │  - research_topic    │
                                   │  - scrape_url        │
                                   │  - summarize_text    │
                                   │  - ask_llm           │
                                   └──────┬───────┬───────┘
                                          │       │
                              ┌───────────┘       └────────────┐
                              ▼                                ▼
                    ┌──────────────────┐            ┌─────────────────┐
                    │   Firecrawl API   │            │  vLLM on Scaleway│
                    │  (web scraping)   │            │  (Llama 3.1 8B)  │
                    │   INTEGRATE       │            │  EXECUTE          │
                    └──────────────────┘            └────────┬────────┘
                                                             │
                                                    ┌────────▼────────┐
                                                    │    Langfuse      │
                                                    │  (observability) │
                                                    │   GOVERN         │
                                                    └─────────────────┘
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/nidhivpatel/ai-research-copilot.git
cd ai-research-copilot
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

| Variable | Description |
|---|---|
| `LLM_BASE_URL` | vLLM endpoint (e.g. `http://<IP>:8000/v1`) or OpenAI (`https://api.openai.com/v1`) |
| `LLM_API_KEY` | API key (`not-needed` for local vLLM) |
| `LLM_MODEL` | Model name (e.g. `meta-llama/Llama-3.1-8B-Instruct` or `gpt-4o-mini`) |
| `FIRECRAWL_API_KEY` | Firecrawl key (free at [firecrawl.dev](https://firecrawl.dev)) — leave empty for httpx fallback |
| `LANGFUSE_PUBLIC_KEY` | Auto-provisioned as `lf_pk_copilot` by docker-compose |
| `LANGFUSE_SECRET_KEY` | Auto-provisioned as `lf_sk_copilot` by docker-compose |
| `LANGFUSE_HOST` | `http://localhost:3000` |

### 3. Start Langfuse

```bash
docker compose up -d
# Dashboard: http://localhost:3000
# Login: admin@copilot.local / copilotadmin
```

The headless init auto-provisions an org, project, and API keys (`lf_pk_copilot` / `lf_sk_copilot`). Add these to your `.env`.

### 4. Test with MCP Inspector

```bash
uv run mcp dev server.py
```

### 5. Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "research-copilot": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ai-research-copilot", "mcp", "run", "server.py"]
    }
  }
}
```

Restart Claude Desktop — you'll see the 4 tools available.

## Tools

| Tool | Description |
|---|---|
| `research_topic(topic, depth=3)` | Search the web, scrape top results, synthesize a structured summary |
| `scrape_url(url)` | Scrape a single URL → clean markdown |
| `summarize_text(text, focus="")` | Summarize text with optional focus area |
| `ask_llm(question, context="")` | Direct LLM question with optional context |

## Demo Flow

1. Open Langfuse dashboard at `localhost:3000`
2. In Claude Desktop, ask: *"Research the latest developments in Kubernetes GPU scheduling"*
   - Claude calls `research_topic` → Firecrawl searches & scrapes → vLLM summarizes
3. Check Langfuse — see the full trace with token counts, latency, and model info
4. Follow up: *"Scrape this blog post and summarize the security implications"*
5. Show Langfuse again — multiple traces, aggregated metrics

## Project Structure

```
server.py          — FastMCP server with 4 tools
scraper.py         — Firecrawl primary + httpx/bs4 fallback
llm_client.py      — Langfuse-traced OpenAI client for vLLM
docker-compose.yml — Langfuse v3 self-hosted stack
.env.example       — Environment variable template
```

## vLLM on Scaleway (optional)

```bash
# On a Scaleway L4-1-24G GPU instance:
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.1-8B-Instruct

# Then set in .env:
LLM_BASE_URL=http://<INSTANCE_IP>:8000/v1
```

Fallback: set `LLM_BASE_URL=https://api.openai.com/v1` and `LLM_MODEL=gpt-4o-mini` to use OpenAI instead.
