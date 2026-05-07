"""LLM client with Langfuse observability — wraps any OpenAI-compatible API."""

from __future__ import annotations

import os

from langfuse import Langfuse
from langfuse.openai import OpenAI

_client: OpenAI | None = None
_langfuse: Langfuse | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.getenv("LLM_API_KEY", "not-needed"),
        )
    return _client


def _flush():
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse()
    _langfuse.flush()


def _model() -> str:
    return os.getenv("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")


def summarize(text: str, instruction: str = "") -> str:
    """Summarize or analyse text using the configured LLM."""
    system = instruction or "Summarize the following content concisely. Highlight key points."
    resp = _get_client().chat.completions.create(
        model=_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text[:12000]},  # guard against huge payloads
        ],
        max_tokens=1024,
    )
    _flush()
    return resp.choices[0].message.content


def chat(messages: list[dict]) -> str:
    """General chat completion."""
    resp = _get_client().chat.completions.create(
        model=_model(),
        messages=messages,
        max_tokens=1024,
    )
    _flush()
    return resp.choices[0].message.content
