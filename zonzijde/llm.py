"""Provider adapters (ARCHITECTURE §6): two named tiers, both driven through
the Claude Agent SDK — each stage invocation is a short agent session with
schema-enforced structured output.

- ``light`` — cheap volume work (S3 scoring): single-prompt, no-tool sessions
  on a Haiku-class model.
- ``frontier`` — curation and writing (S4+): a stronger model; stages may add
  tool use (S5's alternative-coverage search, S6's SRC-3 browsing).

Models are configured in ``config/edition.yaml`` (``llm:``) so they are
swappable without touching stages. Auth is the SDK's own: ``ANTHROPIC_API_KEY``
in env (OPS-5), or ambient Claude Code credentials where the pipeline runs
inside a session.
"""

from __future__ import annotations

import json


class LlmError(RuntimeError):
    """A call failed or returned something unusable; the caller decides
    whether to exclude (fail-closed) or abort."""


def agent_json(prompt: str, *, model: str, system: str | None = None,
               schema: dict | None = None, effort: str | None = None,
               allowed_tools: list[str] | None = None,
               max_turns: int = 1) -> object:
    """One short agent session; returns the parsed JSON response.
    Raises ``LlmError`` on transport failure or an unusable response.

    ``schema`` enforces structured output at the call layer (must be a
    *closed* JSON schema — the API rejects open ``additionalProperties``
    objects). ``effort`` trades reasoning depth for latency/cost per call
    (low…max, None = the model's default).
    """
    import asyncio

    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    kwargs: dict = {"model": model, "effort": effort, "max_turns": max_turns,
                    "allowed_tools": allowed_tools or []}
    if system is not None:
        kwargs["system_prompt"] = system
    if schema is not None:
        kwargs["output_format"] = {"type": "json_schema", "schema": schema}
    options = ClaudeAgentOptions(**kwargs)

    async def run() -> ResultMessage | None:
        result = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message
        return result

    try:
        result = asyncio.run(run())
    except Exception as e:  # SDK/transport errors surface as LlmError
        raise LlmError(f"agent call failed: {type(e).__name__}: {e}")
    if result is None or getattr(result, "is_error", False):
        raise LlmError(f"agent session errored: {result!r:.500}")
    payload = getattr(result, "structured_output", None)
    if payload is not None:
        return payload
    try:
        return json.loads(result.result or "")
    except ValueError as e:
        raise LlmError(f"agent returned non-JSON: {e}: {str(result.result)[:200]!r}")


def light_json(prompt: str, model: str, schema: dict | None = None) -> object:
    """One light-tier call (S3 scoring): single prompt, no tools. Two turns —
    a Haiku-class model needs one to answer and one to emit the structured
    output. Raises ``LlmError`` on failure; the batch is then left unscored
    (fail-closed, PIPE-3)."""
    return agent_json(prompt, model=model, schema=schema, max_turns=2)


def frontier_json(prompt: str, system: str, schema: dict, model: str,
                  effort: str | None = None,
                  allowed_tools: list[str] | None = None,
                  max_turns: int = 2) -> object:
    """One frontier-tier call (S4+). Raises ``LlmError`` on failure — the
    stage fails the run (§6). ``allowed_tools``/``max_turns`` give a stage
    tool use — e.g. WebSearch for S6's SRC-3 browsing. Two turns minimum:
    on a sizeable prompt the model answers in one turn and emits the
    structured output in the next."""
    return agent_json(prompt, model=model, system=system, schema=schema,
                      effort=effort, allowed_tools=allowed_tools,
                      max_turns=max_turns)
