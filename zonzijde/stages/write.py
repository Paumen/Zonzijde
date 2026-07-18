"""S7 write (PIPE-7): one frontier call per article, per the outline.

Reads ``60-outline.json`` + ``50-articles.json``, writes ``70-drafts.json``
and ``70-write-log.json``. Each call is grounded on the slot's own S5 source
texts only; the hard writing rules (``prompts/write.md``) are the system
prompt. The response is schema-enforced at the call layer and grounded here:
paragraph count per ED-4, a loose word-count backstop around the slot's
length guidance, and no self-reference to the paper (PIPE-7) — checked in
code because a regex catches what a prompt merely requests. ``words`` is
computed, never taken from the model. One call per article, no retry: an
article that fails its checks leaves a hole, and an edition with holes fails
the run (§6).

Word counts are guidance, not gates: good content must be written first, and
whether the finished edition needs trimming — or a lesser article cut — is a
compose/gate decision (PIPE-9). The backstop only catches output that
plainly ignored the plan.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         load_artifact, load_model, save_artifact)

# PIPE-7: the paper never refers to itself. (Image/illustration references
# need context to judge — that is S8's review, not a regex.)
SELF_REF_RE = re.compile(r"de zonzijde|deze krant", re.IGNORECASE)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "paragraphs": {"type": "array", "minItems": 1,
                       "items": {"type": "string"}},
    },
    "required": ["title", "paragraphs"],
    "additionalProperties": False,
}

# call(prompt, system) -> parsed JSON; injectable for tests.
FrontierCall = Callable[[str, str], object]


def word_count(paragraphs: list[str]) -> int:
    return len(" ".join(paragraphs).split())


def build_prompt(slot: OutlineSlot, budget: dict, para_cfg: dict,
                 sources: list[ArticleText],
                 others: list[OutlineSlot]) -> str:
    """The plan for this one article + its source texts. The other slots
    appear as titles only, so a 'refer to another article' device (WR-1) has
    something to refer to — never as writing material."""
    plan = [
        f"Edition slot {slot.pos} ({'front page hero' if slot.role == 'front-hero' else 'body'}).",
        f"- topic: {slot.topic}",
        f"- article type: {slot.type}",
        f"- angle: {slot.angle}",
        f"- devices: {', '.join(slot.devices) or 'none'}",
        f"- location (dateline, do not restate in the body): {slot.location}",
        f"- length: {slot.length} — as a guide {budget['min']}–{budget['max']} "
        f"words, {para_cfg['min']}–{para_cfg['max']} paragraphs; the story "
        "decides, not the count",
    ]
    parts = ["\n".join(plan)]
    if others:
        parts.append("Elsewhere in this edition (context only):\n"
                     + "\n".join(f"- slot {o.pos} ({o.scope}): {o.topic}"
                                 for o in others)
                     + "\nA reference device points at such an article by its "
                       "subject — never as 'deze krant' or 'elders in deze "
                       "krant' (PIPE-7).")
    parts.append("Source text(s) — the only writing material:")
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    return "\n\n".join(parts)


def ground(payload: object, slot: OutlineSlot, budget: dict,
           para_cfg: dict, slack: float = 0.0) -> tuple[Draft | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = (payload.get("title") or "").strip() \
        if isinstance(payload.get("title"), str) else ""
    raw = payload.get("paragraphs")
    paragraphs = [p.strip() for p in raw if isinstance(p, str) and p.strip()] \
        if isinstance(raw, list) else []

    problems = []
    if not title:
        problems.append("missing or empty title")
    if not para_cfg["min"] <= len(paragraphs) <= para_cfg["max"]:
        problems.append(f"{len(paragraphs)} paragraphs, needs "
                        f"{para_cfg['min']}–{para_cfg['max']} (ED-4)")
    # The word range is guidance; slack widens it into the backstop that a
    # draft must actually clear. Only output that plainly ignored the plan
    # trips it — fitting the edition happens at compose (PIPE-9).
    words = word_count(paragraphs)
    lo = int(budget["min"] * (1 - slack))
    hi = int(budget["max"] * (1 + slack))
    if not lo <= words <= hi:
        problems.append(f"{words} words — far outside the {slot.length} "
                        f"guidance of {budget['min']}–{budget['max']}")
    hits = {m.group(0) for m in SELF_REF_RE.finditer(" ".join([title] + paragraphs))}
    if hits:
        problems.append("the paper never refers to itself (PIPE-7): "
                        + ", ".join(sorted(hits)))
    if problems:
        return None, problems
    return Draft(pos=slot.pos, title=title, location=slot.location,
                 source_date=slot.source_date, paragraphs=paragraphs,
                 words=words), []


def write_slot(slot: OutlineSlot, articles: dict[str, ArticleText],
               ed_cfg: dict, others: list[OutlineSlot], system: str,
               call: FrontierCall, slack: float = 0.0
               ) -> tuple[Draft | None, list[str]]:
    """Write one article with a single call — no retry. Returns the draft
    (or None if the call failed or the draft missed its checks) plus the
    problems for the log."""
    budget = ed_cfg["words"][slot.length]
    para_cfg = ed_cfg["paragraphs"]
    sources = [articles[sid] for sid in slot.source_ids]
    prompt = build_prompt(slot, budget, para_cfg, sources, others)
    try:
        return ground(call(prompt, system), slot, budget, para_cfg, slack)
    except llm.LlmError as e:
        return None, [str(e)]


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    stage_cfg = ctx.stage_cfg("write")
    concurrency = int(stage_cfg.get("concurrency", 3))
    slack = float(stage_cfg.get("budget_slack", 0.5))
    rules = prompts.load_prompt(ctx.root, "write")
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}

    def work(slot: OutlineSlot) -> tuple[Draft | None, list[str]]:
        others = [s for s in outline.slots if s.pos != slot.pos]
        return write_slot(slot, articles, ed_cfg, others, rules.body, call,
                          slack)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, outline.slots))

    drafts = [d for d, _ in results if d is not None]
    failed = [s.pos for s, (d, _) in zip(outline.slots, results) if d is None]
    log = {
        "model": cfg["model"],
        "prompt_versions": {"write": rules.version},
        "slots": [{"pos": s.pos, "length": s.length,
                   "words": d.words if d else None, "problems": p}
                  for s, (d, p) in zip(outline.slots, results)],
        "words_total": sum(d.words for d in drafts),
        "failed_slots": failed,
    }
    (ctx.work_dir / "70-write-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:  # an edition with holes never advances — the plan counts on
        raise SystemExit(  # every slot (ED-1/ED-2)
            f"S7 write: no valid draft for slot(s) {failed} "
            "— see 70-write-log.json")

    drafts.sort(key=lambda d: d.pos)
    save_artifact(ctx.work_dir / "70-drafts.json", drafts)
    print(f"S7 write: {len(drafts)} articles, {log['words_total']} words "
          f"(ED-5 target {ed_cfg['body_words']['min']}–"
          f"{ed_cfg['body_words']['max']})")
