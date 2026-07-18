"""S8 review (PIPE-8): fact-check each draft against its own source texts.

Reads ``70-drafts.json`` + ``60-outline.json`` (which sources back which
slot) + ``50-articles.json``, writes ``80-reviewed.json`` and
``80-review-log.json`` — the correction log for the edition PR. Per article
one frontier call with ``prompts/review.md`` as system prompt; the response
is schema-enforced and grounded here like S7's, with the same loose word
backstop: the review corrects facts and language (WR-2), it does not re-plan
lengths, but it must not balloon or gut an article either. One call per
article, no retry: a failed article leaves a hole and the run fails (§6).
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         Review, ReviewedArticle, load_artifact, load_model,
                         save_artifact)
from .write import SELF_REF_RE, word_count

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "paragraphs": {"type": "array", "minItems": 1,
                       "items": {"type": "string"}},
        "fact_issues": {"type": "array", "items": {"type": "string"}},
        "corrections": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "paragraphs", "fact_issues", "corrections"],
    "additionalProperties": False,
}

# call(prompt, system) -> parsed JSON; injectable for tests.
FrontierCall = Callable[[str, str], object]


def build_prompt(draft: Draft, slot: OutlineSlot, budget: dict,
                 sources: list[ArticleText]) -> str:
    parts = [
        f"Draft article (slot {draft.pos}, {slot.length}, written to a "
        f"guide of {budget['min']}–{budget['max']} words):",
        f"Titel: {draft.title}",
        "\n\n".join(draft.paragraphs),
        "Source text(s) — the only ground truth (WR-2):",
    ]
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    return "\n\n".join(parts)


def ground(payload: object, draft: Draft, budget: dict, para_cfg: dict,
           slack: float) -> tuple[ReviewedArticle | None, list[str]]:
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
    lo = int(budget["min"] * (1 - slack))
    hi = int(budget["max"] * (1 + slack))
    if not lo <= words <= hi:
        problems.append(f"{words} words after review — far outside the "
                        f"draft's guidance of {budget['min']}–"
                        f"{budget['max']}; correct, don't rewrite")
    hits = {m.group(0) for m in SELF_REF_RE.finditer(" ".join([title] + paragraphs))}
    if hits:
        problems.append("the paper never refers to itself (PIPE-7): "
                        + ", ".join(sorted(hits)))
    if problems:
        return None, problems
    def _strings(key: str) -> list[str]:
        raw = payload.get(key)  # null instead of [] must not crash the stage
        return [s.strip() for s in raw if isinstance(s, str) and s.strip()] \
            if isinstance(raw, list) else []

    review = Review(fact_issues=_strings("fact_issues"),
                    corrections=_strings("corrections"))
    return ReviewedArticle(pos=draft.pos, title=title, location=draft.location,
                           source_date=draft.source_date,
                           paragraphs=paragraphs, words=words,
                           review=review), []


def review_draft(draft: Draft, slot: OutlineSlot,
                 articles: dict[str, ArticleText], ed_cfg: dict, slack: float,
                 system: str, call: FrontierCall
                 ) -> tuple[ReviewedArticle | None, list[str]]:
    """Review one draft with a single call — no retry. Returns the reviewed
    article (or None on call failure / failed checks) plus the problems."""
    budget = ed_cfg["words"][slot.length]
    para_cfg = ed_cfg["paragraphs"]
    sources = [articles[sid] for sid in slot.source_ids]
    prompt = build_prompt(draft, slot, budget, sources)
    try:
        return ground(call(prompt, system), draft, budget, para_cfg, slack)
    except llm.LlmError as e:
        return None, [str(e)]


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    stage_cfg = ctx.stage_cfg("review")
    concurrency = int(stage_cfg.get("concurrency", 3))
    slack = float(stage_cfg.get("budget_slack", 0.5))
    rules = prompts.load_prompt(ctx.root, "review")
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    drafts = load_artifact(ctx.work_dir / "70-drafts.json", Draft)
    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    slots = {s.pos: s for s in outline.slots}
    missing = [d.pos for d in drafts if d.pos not in slots]
    if missing:
        raise SystemExit(f"S8 review: draft slot(s) {missing} not in the "
                         "outline — artifacts out of step, re-run S6/S7")
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}

    def work(draft: Draft) -> tuple[ReviewedArticle | None, list[str]]:
        return review_draft(draft, slots[draft.pos], articles, ed_cfg, slack,
                            rules.body, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, drafts))

    reviewed = [r for r, _ in results if r is not None]
    failed = [d.pos for d, (r, _) in zip(drafts, results) if r is None]
    log = {
        "model": cfg["model"],
        "prompt_versions": {"review": rules.version},
        "articles": [{"pos": d.pos,
                      "words": {"draft": d.words,
                                "reviewed": r.words if r else None},
                      "fact_issues": r.review.fact_issues if r else [],
                      "corrections": r.review.corrections if r else [],
                      "problems": p}
                     for d, (r, p) in zip(drafts, results)],
        "words_total": sum(r.words for r in reviewed),
        "failed_slots": failed,
    }
    (ctx.work_dir / "80-review-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(
            f"S8 review: no valid review for slot(s) {failed} "
            "— see 80-review-log.json")

    reviewed.sort(key=lambda r: r.pos)
    save_artifact(ctx.work_dir / "80-reviewed.json", reviewed)
    issues = sum(len(r.review.fact_issues) for r in reviewed)
    corrections = sum(len(r.review.corrections) for r in reviewed)
    print(f"S8 review: {len(reviewed)} articles, {issues} fact issue(s), "
          f"{corrections} correction(s), {log['words_total']} words")
