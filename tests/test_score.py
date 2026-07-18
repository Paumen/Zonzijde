"""S3 score: batch prompt format, response validation, fail-closed exclusion."""

import json
from datetime import datetime

from zonzijde import llm
from zonzijde.context import TZ
from zonzijde.contracts import FeedItem, ScoredItem, load_artifact, save_artifact
from zonzijde.stages.score import (build_batch_prompt, item_line, parse_scores,
                                   run, score_batch)


def _item(n: int, title: str = "Titel", summary: str = "Samenvatting") -> FeedItem:
    return FeedItem(
        id=f"{n:012d}", source="gld_rvn", bron="Gld RvN", scopes=["L", "R"],
        title=title, link=f"https://x.nl/{n}", summary=summary, published=None,
        fetched=datetime(2026, 7, 18, 6, 0, tzinfo=TZ))


def test_item_line_matches_prototype_format():
    # title — summary, whitespace collapsed, capped at 500 chars; a
    # summary-less item is just the title (ported behaviour).
    assert item_line(3, _item(1, "Kop  met\nwitregels", "Meer  tekst")) == \
        "3. Kop met witregels — Meer tekst"
    assert item_line(1, _item(1, "Alleen kop", "")) == "1. Alleen kop"
    assert len(item_line(1, _item(1, "x" * 600, ""))) == len("1. ") + 500


def test_build_batch_prompt_numbers_from_one():
    prompt = build_batch_prompt("INSTRUCTIE", [_item(1), _item(2)])
    assert prompt.startswith("INSTRUCTIE\n1. ")
    assert "\n2. " in prompt


def test_parse_scores_accepts_exact_response():
    scores, problems = parse_scores({"1": -2, "2": 0, "3": 2}, 3)
    assert (scores, problems) == ({1: -2, 2: 0, 3: 2}, [])


def test_parse_scores_flags_contract_violations():
    _, problems = parse_scores({"1": 3}, 2)          # invalid value + missing 2
    assert any("invalid score" in p for p in problems)
    assert any("missing items" in p for p in problems)
    _, problems = parse_scores({"1": True}, 1)       # bool is not a score
    assert any("invalid score" in p for p in problems)
    _, problems = parse_scores({"1": 1, "5": 1}, 2)  # key out of 1..n
    assert any("out of range" in p for p in problems)
    _, problems = parse_scores([1, 2], 2)
    assert problems == ["not a JSON object: list"]


def test_score_batch_retries_once_then_keeps_valid_subset():
    responses = iter([llm.LlmError("boom"), {"1": 2, "2": "hoog"}])

    def call(prompt):
        r = next(responses)
        if isinstance(r, Exception):
            raise r
        return r

    scores, problems = score_batch("P", [_item(1), _item(2)], call)
    assert scores == {1: 2}          # valid subset of the retry survives
    assert problems                  # …and the leftover problem is reported


def test_run_is_fail_closed(tmp_ctx):
    items = [_item(1, "Goed nieuws"), _item(2, "Twijfel"), _item(3, "Meer")]
    save_artifact(tmp_ctx.work_dir / "20-filtered.json", items)

    # Both attempts return item 2 unscored; 1 and 3 valid.
    def call(prompt):
        return {"1": 2, "3": -1}

    run(tmp_ctx, call=call)
    scored = load_artifact(tmp_ctx.work_dir / "30-scored.json", ScoredItem)
    assert [(s.id, s.score) for s in scored] == [(items[0].id, 2), (items[2].id, -1)]
    log = json.loads((tmp_ctx.work_dir / "30-score-log.json").read_text())
    assert log["unscored_ids"] == [items[1].id]
    assert log["distribution"] == {"-2": 0, "-1": 1, "0": 0, "1": 0, "2": 1}
    assert log["prompt_version"] == 1


def test_make_call_unwraps_structured_rows(monkeypatch):
    from zonzijde.stages import score as score_mod

    def fake_light(prompt, model, schema=None):
        assert model == "haiku-test"
        assert schema is score_mod.RESPONSE_SCHEMA  # closed schema, enforced
        return {"scores": [{"i": 1, "score": 2}, {"i": 2, "score": 0}]}

    monkeypatch.setattr(score_mod.llm, "light_json", fake_light)
    call = score_mod.make_call({"model": "haiku-test"})
    payload = call("prompt")
    assert payload == {"1": 2, "2": 0}
    assert parse_scores(payload, 2) == ({1: 2, 2: 0}, [])


def test_unwrap_passes_junk_through_for_parse_scores(monkeypatch):
    from zonzijde.stages.score import _unwrap_scores
    assert _unwrap_scores(["nee"]) == ["nee"]
    assert parse_scores(_unwrap_scores(["nee"]), 1)[1]  # reported, not raised
