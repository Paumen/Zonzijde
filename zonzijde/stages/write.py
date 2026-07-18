"""S7 write (PIPE-7): one frontier call per article, per the outline.

Reads ``60-outline.json`` + ``50-articles.json``, writes ``70-drafts.json``
and ``70-write-log.json``. Each call is grounded on the slot's own S5 source
texts only; the hard writing rules (``prompts/write.md``) are the system
prompt. The response is schema-enforced at the call layer and grounded here:
paragraph count per ED-4, word count within the slot's length-class budget,
and no self-reference to the paper (PIPE-7) — checked in code because a
regex catches what a prompt merely requests. ``words`` is computed, never
taken from the model. Retries with feedback per article, fatal after 3 (§6).
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         load_artifact, load_model, save_artifact)

MAX_ATTEMPTS = 3
BACKOFF_S = 2.0

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
        f"- length: {slot.length} — {budget['min']}–{budget['max']} words, "
        f"{para_cfg['min']}–{para_cfg['max']} paragraphs",
    ]
    parts = ["\n".join(plan)]
    if others:
        parts.append("Elsewhere in this edition (context only):\n"
                     + "\n".join(f"- slot {o.pos} ({o.scope}): {o.topic}"
                                 for o in others))
    parts.append("Source text(s) — the only writing material:")
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    return "\n\n".join(parts)


def ground(payload: object, slot: OutlineSlot, budget: dict,
           para_cfg: dict) -> tuple[Draft | None, list[str]]:
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
    words = word_count(paragraphs)
    if not budget["min"] <= words <= budget["max"]:
        problems.append(f"{words} words, budget is "
                        f"{budget['min']}–{budget['max']} ({slot.length})")
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
               call: FrontierCall) -> tuple[Draft | None, list[dict]]:
    """Write one article with the per-article retry policy. Returns the
    draft (or None after MAX_ATTEMPTS) plus the attempt log."""
    budget = ed_cfg["words"][slot.length]
    para_cfg = ed_cfg["paragraphs"]
    sources = [articles[sid] for sid in slot.source_ids]
    prompt = build_prompt(slot, budget, para_cfg, sources, others)
    attempts = []
    draft = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        call_failed = False
        try:
            draft, problems = ground(call(prompt, system), slot, budget, para_cfg)
        except llm.LlmError as e:
            draft, problems = None, [str(e)]
            call_failed = True
        attempts.append({"attempt": attempt, "problems": problems})
        if not problems:
            break
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S * 2 ** (attempt - 1))
            prompt = build_prompt(slot, budget, para_cfg, sources, others)
            if not call_failed:
                prompt += ("\n\nYour previous draft was invalid:\n- "
                           + "\n- ".join(problems) + "\nCorrect this.")
    return draft, attempts


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    concurrency = int(ctx.stage_cfg("write").get("concurrency", 3))
    rules = prompts.load_prompt(ctx.root, "write")
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}

    def work(slot: OutlineSlot) -> tuple[Draft | None, list[dict]]:
        others = [s for s in outline.slots if s.pos != slot.pos]
        return write_slot(slot, articles, ed_cfg, others, rules.body, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, outline.slots))

    drafts = [d for d, _ in results if d is not None]
    failed = [s.pos for s, (d, _) in zip(outline.slots, results) if d is None]
    log = {
        "model": cfg["model"],
        "prompt_versions": {"write": rules.version},
        "slots": [{"pos": s.pos, "length": s.length,
                   "words": d.words if d else None, "attempts": a}
                  for s, (d, a) in zip(outline.slots, results)],
        "words_total": sum(d.words for d in drafts),
        "failed_slots": failed,
    }
    (ctx.work_dir / "70-write-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:  # an edition with holes never advances — the plan counts on
        raise SystemExit(  # every slot (ED-1/ED-2)
            f"S7 write: no valid draft after {MAX_ATTEMPTS} attempts for "
            f"slot(s) {failed} — see 70-write-log.json")

    drafts.sort(key=lambda d: d.pos)
    save_artifact(ctx.work_dir / "70-drafts.json", drafts)
    print(f"S7 write: {len(drafts)} articles, {log['words_total']} words "
          f"(ED-5 target {ed_cfg['body_words']['min']}–"
          f"{ed_cfg['body_words']['max']})")
