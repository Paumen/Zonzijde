"""Provider adapters (ARCHITECTURE §6): two named tiers.

- ``light`` — the Gemini API called directly: plain batched JSON-mode calls
  at temperature 0, no agent loop needed (S3 scoring).
- ``frontier`` — driven through the Claude Agent SDK: each stage invocation
  is a short agent session with schema-enforced structured output (S4+;
  later stages get browsing/tool use from the same adapter).

Models are configured in ``config/edition.yaml`` (``llm:``) so they are
swappable without touching stages. Keys live in env only — ``GEMINI_API_KEY``
and ``ANTHROPIC_API_KEY`` — never in the repo (OPS-5).
"""

from __future__ import annotations

import json
import os

import requests

from .net import VERIFY

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"


class LlmError(RuntimeError):
    """A call failed or returned something unusable; the caller decides
    whether to retry, exclude (fail-closed) or abort."""


def require_key(name: str) -> str:
    key = os.environ.get(name, "")
    if not key:
        raise SystemExit(f"{name} is not set — keys live in env only (OPS-5)")
    return key


def light_json(prompt: str, model: str, timeout: float = 120.0) -> object:
    """One JSON-mode Gemini call at temperature 0; returns the parsed JSON.

    Raises ``LlmError`` on transport failure or an unparseable response —
    the S3 caller retries once and then leaves the batch unscored (PIPE-3).
    """
    key = require_key("GEMINI_API_KEY")
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0},
    }
    try:
        res = requests.post(
            f"{GEMINI_BASE}{model}:generateContent",
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=body, timeout=timeout, verify=VERIFY)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError) as e:
        raise LlmError(f"gemini call failed: {type(e).__name__}: {e}")
    parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts)
    try:
        return json.loads(text)
    except ValueError as e:
        raise LlmError(f"gemini returned non-JSON: {e}: {text[:200]!r}")


def frontier_json(prompt: str, system: str, schema: dict, model: str) -> object:
    """One short Claude Agent SDK session with schema-enforced structured
    output; returns the parsed JSON. Raises ``LlmError`` on failure —
    the S4 caller retries with backoff and is fatal after 3 (§6).

    ``ANTHROPIC_API_KEY`` is read from env by the SDK itself.
    """
    import asyncio

    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    options = ClaudeAgentOptions(
        system_prompt=system, model=model, max_turns=1, allowed_tools=[],
        output_format={"type": "json_schema", "schema": schema})

    async def run() -> ResultMessage | None:
        result = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message
        return result

    try:
        result = asyncio.run(run())
    except Exception as e:  # SDK/transport errors are all retryable here
        raise LlmError(f"frontier call failed: {type(e).__name__}: {e}")
    if result is None or getattr(result, "is_error", False):
        raise LlmError(f"frontier session errored: {result!r:.500}")
    payload = getattr(result, "structured_output", None)
    if payload is not None:
        return payload
    try:
        return json.loads(result.result or "")
    except ValueError as e:
        raise LlmError(f"frontier returned non-JSON: {e}: {str(result.result)[:200]!r}")
