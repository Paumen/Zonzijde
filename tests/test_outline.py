"""S6 outline: no validation of the model's editorial choices — the plan is
built as-is. Code still owns ring order (ED-6) and pos/role/source_date;
only the pydantic contract stands. Single call, fatal on unusable output."""

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


def _published() -> dict:
    return {_id(n): date(2026, 7, 10 + (n % 5)) for n in SCOPE_OF}


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
        _payload(), EDITION, _cfg(tmp_ctx), _articles(), _published())
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


def test_ground_takes_editorial_choices_as_is(tmp_ctx):
    # ED-1/ED-2 counts, an unknown source id, a blocked source, a scope
    # mismatch — none are validated now. The plan builds as the model gave it.
    payload = _payload()
    for s in payload["slots"]:
        s["length"] = "standard"                  # ED-2 mix ignored
    payload["slots"] += [_slot(3), _slot(3)]       # 4 lokaal — ED-1 ignored
    payload["slots"][0]["source_ids"] = ["ffffffffffff"]  # unknown id, ok
    result, problems = outline.ground(
        payload, EDITION, _cfg(tmp_ctx), _articles(ok_all=False), _published())
    assert problems == []
    assert len(result.slots) == 10
    # an unknown/undated source just yields no source_date, never a rejection
    assert result.slots[0].source_date is None


def test_ground_defaults_a_bad_illustration_index(tmp_ctx):
    # Out-of-range illustration slot_index is not rejected — it falls back to
    # the first slot so the plan still builds.
    payload = _payload()
    payload["illustration"]["slot_index"] = 99
    result, problems = outline.ground(
        payload, EDITION, _cfg(tmp_ctx), _articles(), _published())
    assert problems == []
    assert result.illustration.slot_pos == 1


def test_ground_needs_source_ids_for_the_contract(tmp_ctx):
    # A slot with no source_ids can't satisfy the OutlineSlot contract
    # (min_length 1) — that surfaces as an unusable-response problem.
    payload = _payload()
    payload["slots"][0]["source_ids"] = []
    _, problems = outline.ground(
        payload, EDITION, _cfg(tmp_ctx), _articles(), _published())
    assert any("invalid outline" in p for p in problems)


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
    assert "Shortlist" in seen["prompt"] and "samenvatting=" in seen["prompt"]
    assert "woord" not in seen["prompt"]            # full texts are NOT inline

    result = load_model(tmp_ctx.work_dir / "60-outline.json", EditionOutline)
    assert result.edition == tmp_ctx.edition
    assert len(result.slots) == 8
    log = json.loads((tmp_ctx.work_dir / "60-outline-log.json").read_text())
    assert log["prompt_versions"]["outline"] >= 2
    assert log["planned_words"]["min"] > 0


def test_unusable_response_is_fatal_single_call(tmp_ctx):
    _seed_work(tmp_ctx)
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        return {"slots": "nee"}

    with pytest.raises(SystemExit, match="unusable response"):
        outline.run(tmp_ctx, call=call)
    assert len(calls) == 1  # one call, no retry
