from __future__ import annotations

import json


class LlmError(RuntimeError):
    pass


def _record_usage(result: object, tool_uses: int, thinking_chars: int) -> dict:
    raw = getattr(result, "usage", None)

    def field(name: str) -> object:
        if isinstance(raw, dict):
            return raw.get(name)
        return getattr(raw, name, None)

    def num(value: object) -> int:
        return int(value) if isinstance(value, (int, float)) else 0

    cost = getattr(result, "total_cost_usd", None)
    return {
        "input_tokens": num(field("input_tokens")),
        "output_tokens": num(field("output_tokens")),
        "cache_read_tokens": num(field("cache_read_input_tokens")),
        "cache_creation_tokens": num(field("cache_creation_input_tokens")),
        "cost_usd": float(cost) if isinstance(cost, (int, float)) else None,
        "turns": num(getattr(result, "num_turns", None)),
        "wall_ms": num(getattr(result, "duration_ms", None)),
        "api_ms": num(getattr(result, "duration_api_ms", None)),
        "tool_uses": tool_uses,
        "thinking_chars": thinking_chars,
    }


def summarize_usage(records: list[dict] | None) -> dict | None:
    recs = [r for r in (records or []) if r]
    if not recs:
        return None

    def total(name: str) -> int:
        return sum((r.get(name) or 0) for r in recs)

    costs = [r.get("cost_usd") for r in recs if isinstance(r.get("cost_usd"), (int, float))]
    return {
        "calls": len(recs),
        "input_tokens": total("input_tokens"),
        "output_tokens": total("output_tokens"),
        "cache_read_tokens": total("cache_read_tokens"),
        "cache_creation_tokens": total("cache_creation_tokens"),
        "cost_usd": round(sum(costs), 4) if costs else None,
        "turns": total("turns"),
        "tool_uses": total("tool_uses"),
        "thinking_chars": total("thinking_chars"),
        "wall_ms": total("wall_ms"),
        "api_ms": total("api_ms"),
    }


def agent_json(prompt: str, *, model: str, system: str | None = None,
               schema: dict | None = None, effort: str | None = None,
               allowed_tools: list[str] | None = None,
               permission_mode: str | None = None, cwd: str | None = None,
               max_turns: int = 1, usage_sink: list | None = None) -> object:
    import asyncio

    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    kwargs: dict = {"model": model, "effort": effort, "max_turns": max_turns,
                    "allowed_tools": allowed_tools or []}
    if permission_mode is not None:
        kwargs["permission_mode"] = permission_mode
    if cwd is not None:
        kwargs["cwd"] = cwd
    if system is not None:
        kwargs["system_prompt"] = system
    if schema is not None:
        kwargs["output_format"] = {"type": "json_schema", "schema": schema}
    options = ClaudeAgentOptions(**kwargs)

    async def run() -> tuple[object, int, int]:
        result = None
        tool_uses = 0
        thinking_chars = 0
        async for message in query(prompt=prompt, options=options):
            content = getattr(message, "content", None)
            if isinstance(content, list):
                for block in content:
                    name = type(block).__name__
                    if name == "ToolUseBlock":
                        tool_uses += 1
                    elif name == "ThinkingBlock":
                        thinking_chars += len(getattr(block, "thinking", "") or "")
            if isinstance(message, ResultMessage):
                result = message
        return result, tool_uses, thinking_chars

    try:
        result, tool_uses, thinking_chars = asyncio.run(run())
    except Exception as e:
        raise LlmError(f"agent call failed: {type(e).__name__}: {e}")
    if result is None or getattr(result, "is_error", False):
        raise LlmError(f"agent session errored: {result!r:.500}")
    if usage_sink is not None:
        usage_sink.append(_record_usage(result, tool_uses, thinking_chars))
    payload = getattr(result, "structured_output", None)
    if payload is not None:
        return payload
    try:
        return json.loads(result.result or "")
    except ValueError as e:
        raise LlmError(f"agent returned non-JSON: {e}: {str(result.result)[:200]!r}")
