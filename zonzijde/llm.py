from __future__ import annotations

import json


class LlmError(RuntimeError):
    pass


def agent_json(prompt: str, *, model: str, system: str | None = None,
               schema: dict | None = None, effort: str | None = None,
               allowed_tools: list[str] | None = None,
               max_turns: int = 1) -> object:
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
    except Exception as e:
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
    return agent_json(prompt, model=model, schema=schema, max_turns=2)


def frontier_json(prompt: str, system: str, schema: dict, model: str,
                  effort: str | None = None,
                  allowed_tools: list[str] | None = None,
                  max_turns: int = 2) -> object:
    return agent_json(prompt, model=model, system=system, schema=schema,
                      effort=effort, allowed_tools=allowed_tools,
                      max_turns=max_turns)
