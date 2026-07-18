"""S6 outline: grounding against ED-1/ED-2/ED-6, ring order by construction,
code-derived pos/role/source_date, retry-then-fatal, artifact writing."""

import json
from datetime import date

import pytest

from tests.conftest import make_article, make_candidate, make_scored
from zonzijde.contracts import EditionOutline, load_model, save_artifact
from zonzijde.stages import outline

EDITION = date(2026, 7, 26)

# 12 topics, 3 per scope, one source article each: L=1..3, R=4..6, N=7..9,
# I=10..12.
SCOPE_OF = {n: s for s, ns in
            {"L": [1, 2, 3], "R": [4, 5, 6],
             "N": [7, 8, 9], "I": [10, 11, 12]}.items() for n in ns}


def _id(n: int) -> str:
    return f"{n:012d}"


def _articles(ok_all: bool = True) -> dict:
    return {_id(n): make_article(n, ok=ok_all or n != 3) for n in SCOPE_OF}


def _scopes_by_id() -> dict:
    return {_id(n): {s} for n, s in SCOPE_OF.items()}


def _published() -> dict:
    return {_id(n): date(2026, 7, 10 + (n % 5)) for n in SCOPE_OF}


def _available(n_per_scope: int = 3) -> dict:
    return {s: n_per_scope for s in "LRNI"}


def _slot(n: int, length: str = "standard") -> dict:
    return {"scope": SCOPE_OF[n], "topic": f"Topic {n}", "length": length,
            "type": "news", "angle": "hoek", "devices": [],
            "source_ids": [_id(n)], "location": "Wijchen"}


def _payload() -> dict:
    # Deliberately out of ring order: grounding must sort, not reject.
    # Mix: 2 long, 4 standard, 2 short (ED-2 ✓); 2 per scope (ED-1 ✓).
    return {
        "slots": [_slot(4), _slot(1, "long"), _slot(2, "short"), _slot(5),
                  _slot(7, "long"), _slot(8), _slot(10, "short"), _slot(11)],
        "illustration": {"slot_index": 5, "subject": "een robotpak"},
        "optional_element": {"kind": "none", "content": ""},
    }


def _cfg(ctx) -> dict:
    return ctx.edition_cfg


def test_ground_sorts_into_ring_order_and_derives_fields(tmp_ctx):
    result, problems = outline.ground(
        _payload(), EDITION, _cfg(tmp_ctx), _articles(), _scopes_by_id(),
        _published(), _available())
    assert problems == []
    assert [s.scope for s in result.slots] == list("LLRRNNII")  # ED-6
    assert [s.pos for s in result.slots] == list(range(1, 9))
    assert result.slots[0].role == "front-hero"
    assert result.slots[0].source_ids == [_id(1)]  # model's first L leads
    assert all(s.role == "body" for s in result.slots[1:])
    # source_date = published date of the slot's source (ED-3)
    assert result.slots[0].source_date == _published()[_id(1)]
    # illustration slot_index 5 pointed at N7 → pos 5 after the sort
    assert result.illustration.slot_pos == 5


def test_ground_rejects_unknown_blocked_or_wrong_scope_sources(tmp_ctx):
    args = (EDITION, _cfg(tmp_ctx), _articles(ok_all=False),
            _scopes_by_id(), _published(), _available())

    payload = _payload()
    payload["slots"][0]["source_ids"] = ["ffffffffffff"]
    _, problems = outline.ground(payload, *args)
    assert any("unknown source id" in p for p in problems)

    payload = _payload()
    payload["slots"][1]["source_ids"] = [_id(3)]  # article 3 is not ok
    _, problems = outline.ground(payload, *args)
    assert any("no full text" in p for p in problems)

    payload = _payload()
    payload["slots"][0]["source_ids"] = [_id(1)]  # L article in an R slot
    _, problems = outline.ground(payload, *args)
    assert any("does not back a R topic" in p for p in problems)


def test_ground_enforces_scope_counts_and_length_mix(tmp_ctx):
    args = (EDITION, _cfg(tmp_ctx), _articles(), _scopes_by_id(),
            _published(), _available())

    payload = _payload()
    payload["slots"] += [_slot(3), _slot(3)]  # lokaal now has four slots
    _, problems = outline.ground(payload, *args)
    assert any("at most 3 (ED-1)" in p for p in problems)

    payload = _payload()
    for s in payload["slots"]:
        s["length"] = "standard"  # no long, no short, 8 standard
    _, problems = outline.ground(payload, *args)
    assert sum("(ED-2)" in p for p in problems) == 3

    payload = _payload()
    payload["slots"] = [s for s in payload["slots"] if s["scope"] != "I"]
    _, problems = outline.ground(payload, *args)
    assert any("internationaal: 0 items" in p for p in problems)


def test_ground_relaxes_scope_minimum_to_what_survived(tmp_ctx):
    # Only one I topic survived S5 → one I slot is acceptable (the drop log
    # made the shortfall visible; the gate judges the thinner edition).
    available = {"L": 3, "R": 3, "N": 3, "I": 1}
    payload = _payload()
    payload["slots"] = [s for s in payload["slots"]
                        if s != _slot(11)] + [_slot(6)]
    result, problems = outline.ground(
        payload, EDITION, _cfg(tmp_ctx), _articles(), _scopes_by_id(),
        _published(), available)
    assert problems == []
    assert sum(1 for s in result.slots if s.scope == "I") == 1


def test_ground_rejects_reused_source_and_bad_illustration(tmp_ctx):
    args = (EDITION, _cfg(tmp_ctx), _articles(), _scopes_by_id(),
            _published(), _available())

    payload = _payload()
    payload["slots"][3]["source_ids"] = [_id(4)]  # already used by slot 0
    _, problems = outline.ground(payload, *args)
    assert any("more than one slot" in p for p in problems)

    payload = _payload()
    payload["illustration"]["slot_index"] = 99
    _, problems = outline.ground(payload, *args)
    assert any("does not point at a slot" in p for p in problems)


def test_ground_rejects_missing_or_null_source_ids(tmp_ctx):
    # A slot without usable source_ids is a problem, never a crash.
    args = (EDITION, _cfg(tmp_ctx), _articles(), _scopes_by_id(),
            _published(), _available())
    for bad in (None, [], "nee"):
        payload = _payload()
        payload["slots"][0]["source_ids"] = bad
        _, problems = outline.ground(payload, *args)
        assert any("missing source_ids" in p for p in problems), bad
    payload = _payload()
    del payload["slots"][0]["source_ids"]
    _, problems = outline.ground(payload, *args)
    assert any("missing source_ids" in p for p in problems)


def _seed_work(ctx) -> None:
    candidates = [make_candidate(SCOPE_OF[n], (n - 1) % 3 + 1, [n])
                  for n in SCOPE_OF]
    save_artifact(ctx.work_dir / "40-candidates.json", candidates)
    save_artifact(ctx.work_dir / "50-articles.json",
                  [make_article(n) for n in SCOPE_OF])
    save_artifact(ctx.work_dir / "30-scored.json",
                  [make_scored(n, SCOPE_OF[n]) for n in SCOPE_OF])
    (ctx.work_dir / "50-enrich-log.json").write_text(
        json.dumps({"dropped_topics": []}))


def test_run_writes_outline_and_log(tmp_ctx):
    _seed_work(tmp_ctx)
    seen = {}

    def call(prompt, system):
        seen["prompt"], seen["system"] = prompt, system
        return _payload()

    outline.run(tmp_ctx, call=call)
    assert "People are worn out" in seen["system"]  # brief.md is the system
    assert "Edition constants (SPEC §5)" in seen["prompt"]
    assert "woord" in seen["prompt"]                # full texts are inline

    result = load_model(tmp_ctx.work_dir / "60-outline.json", EditionOutline)
    assert result.edition == tmp_ctx.edition
    assert len(result.slots) == 8
    log = json.loads((tmp_ctx.work_dir / "60-outline-log.json").read_text())
    assert log["prompt_versions"]["outline"] >= 2
    assert log["planned_words"]["min"] > 0
    assert [a["attempt"] for a in log["attempts"]] == [1]


def test_run_feeds_problems_back_then_fatal(tmp_ctx, monkeypatch):
    monkeypatch.setattr(outline.time, "sleep", lambda s: None)
    _seed_work(tmp_ctx)
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        return {"slots": "nee"}

    with pytest.raises(SystemExit, match="no valid edition plan after 3"):
        outline.run(tmp_ctx, call=call)
    assert len(calls) == 3
    assert "previous plan was invalid" in calls[1]


def test_run_requires_surviving_topics(tmp_ctx):
    candidates = [make_candidate("L", 1, [1])]
    save_artifact(tmp_ctx.work_dir / "40-candidates.json", candidates)
    save_artifact(tmp_ctx.work_dir / "50-articles.json",
                  [make_article(1, ok=False)])
    save_artifact(tmp_ctx.work_dir / "30-scored.json", [make_scored(1, "L")])
    (tmp_ctx.work_dir / "50-enrich-log.json").write_text(
        json.dumps({"dropped_topics": ["Topic 1"]}))
    with pytest.raises(SystemExit, match="no topic survived"):
        outline.run(tmp_ctx, call=lambda p, s: _payload())
