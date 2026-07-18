"""S5 enrich: two-stage fetch, no summary fallback, re-source-or-drop."""

import json

import pytest

from zonzijde.contracts import (ArticleText, Candidate, CandidateItem,
                                load_artifact, save_artifact)
from zonzijde.stages import enrich

# ~150 words of body text: enough to clear the min_words gate (default 120).
PARAGRAPH = ("De vrijwilligers van de speeltuin hebben afgelopen zaterdag "
             "samen met tientallen buurtbewoners de nieuwe toestellen "
             "geplaatst en het terrein feestelijk geopend voor alle "
             "kinderen uit de wijk en omliggende dorpen. ") * 3
BODY = "\n".join(f"<p>{PARAGRAPH}</p>" for _ in range(3))


def _html(body: str = BODY) -> str:
    return ("<html><head><title>Speeltuin geopend</title></head>"
            f"<body><main><article>{body}</article></main></body></html>")


def _item(n: int, host: str | None = None) -> CandidateItem:
    return CandidateItem(id=f"{n:012d}", bron=f"Bron{n}", titel=f"Titel {n}",
                         samenvatting="RSS-blurb die nooit kopij wordt",
                         link=f"https://{host or f'site{n}.nl'}/artikel-{n}")


def _cand(scope="L", rank=1, topic="Onderwerp", items=None) -> Candidate:
    return Candidate(scope=scope, rank=rank, topic=topic,
                     items=items or [_item(rank)])


def _no_render(blocked, timeout, min_words):
    return 0


def _no_search(query, timeout, max_results):
    return []


def test_extract_returns_text_and_in_article_links():
    body = BODY + '<p>Lees ook <a href="https://voorbeeld.nl/x">dit verhaal</a>.</p>'
    text, links = enrich.extract(_html(body), "https://site1.nl/artikel-1")
    assert len(text.split()) > 120
    assert "https://voorbeeld.nl/x" in links


def test_run_happy_path_writes_articles_and_log(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json",
                  [_cand(), _cand(scope="N", rank=1, topic="Landelijk",
                                  items=[_item(2)])])

    def boom(*a):
        raise AssertionError("nothing was blocked — render must not run")

    enrich.run(tmp_ctx, fetch=lambda url, t: (200, _html()),
               render=boom, search=_no_search)
    arts = load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)
    assert [a.ok for a in arts] == [True, True]
    assert all(a.method == "requests" and a.words >= 120 for a in arts)
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    assert log["full_text"] == 2 and log["dropped_topics"] == []


def test_blocked_link_goes_to_browser_render(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json",
                  [_cand(items=[_item(1), _item(2)])])
    seen = []

    def render(blocked, timeout, min_words):
        seen.extend(a.id for a in blocked)
        for a in blocked:
            text, links = enrich.extract(_html(), a.link)
            a.ok, a.method, a.text = True, "playwright", text
            a.words, a.links, a.note = len(text.split()), links, ""
        return len(blocked)

    def fetch(url, t):  # site1 blocks the plain client, site2 doesn't
        return (403, "<html>verboden</html>") if "site1" in url else (200, _html())

    enrich.run(tmp_ctx, fetch=fetch, render=render, search=_no_search)
    assert seen == ["000000000001"]  # only the blocked row went to the browser
    arts = {a.id: a for a in
            load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)}
    assert arts["000000000001"].method == "playwright"
    assert arts["000000000002"].method == "requests"


def test_fully_blocked_topic_is_dropped_without_summary_fallback(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json", [_cand()])
    enrich.run(tmp_ctx, fetch=lambda url, t: (403, "<html>nee</html>"),
               render=_no_render, search=_no_search)
    (art,) = load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)
    assert not art.ok
    assert art.text == ""  # PIPE-5: the RSS samenvatting never becomes text
    assert "topic dropped (PIPE-5)" in art.note
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    assert log["dropped_topics"] == ["Onderwerp"]
    assert log["topics"][0]["alt_search"]["query"] == "Titel 1"


def test_surviving_sibling_row_skips_the_search(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json",
                  [_cand(items=[_item(1), _item(2)])])

    def fetch(url, t):
        return (200, _html()) if "site2" in url else (403, "")

    def boom(*a):
        raise AssertionError("sibling row has full text — no search needed")

    enrich.run(tmp_ctx, fetch=fetch, render=_no_render, search=boom)
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    topic = log["topics"][0]
    assert (topic["ok_rows"], topic["dropped"], topic["alt_search"]) == (1, False, None)


def test_alt_source_recovers_a_blocked_topic(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json", [_cand()])
    alt = "https://andere-krant.nl/zelfde-verhaal"

    def fetch(url, t):
        return (200, _html()) if url == alt else (403, "")

    def search(query, timeout, max_results):
        assert query == "Titel 1"
        return ["https://site1.nl/andere-pagina", alt]  # own host first

    enrich.run(tmp_ctx, fetch=fetch, render=_no_render, search=search)
    (art,) = load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)
    assert art.ok and art.method == "alt-source"
    assert alt in art.note
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    assert log["topics"][0]["dropped"] is False
    assert log["topics"][0]["alt_search"]["tried"] == [alt]  # own host skipped
    assert log["topics"][0]["alt_search"]["picked"] == alt


def test_extraction_crash_blocks_the_row_not_the_stage(tmp_ctx, monkeypatch):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json", [_cand()])

    def broken_extract(html, url):
        raise ValueError("kapotte HTML")

    monkeypatch.setattr(enrich, "extract", broken_extract)
    enrich.run(tmp_ctx, fetch=lambda u, t: (200, "<html>"),
               render=_no_render, search=_no_search)
    (art,) = load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)
    assert not art.ok and "extraction failed: ValueError" in art.note


def test_alt_source_skips_www_variant_of_own_host(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json",
                  [_cand(items=[_item(1, host="www.site1.nl")])])
    enrich.run(tmp_ctx, fetch=lambda u, t: (403, ""), render=_no_render,
               search=lambda q, t, n: ["https://SITE1.nl/andere-pagina"])
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    assert log["topics"][0]["alt_search"]["tried"] == []  # same host, skipped


def test_shared_item_is_fetched_once(tmp_ctx):
    shared = _item(1)
    save_artifact(tmp_ctx.work_dir / "40-candidates.json",
                  [_cand(items=[shared]),
                   _cand(scope="R", topic="Regionaal", items=[shared])])
    calls = []

    def fetch(url, t):
        calls.append(url)
        return 200, _html()

    enrich.run(tmp_ctx, fetch=fetch, render=_no_render, search=_no_search)
    assert calls == [shared.link]
    arts = load_artifact(tmp_ctx.work_dir / "50-articles.json", ArticleText)
    assert len(arts) == 1


def test_empty_candidates_is_fatal(tmp_ctx):
    (tmp_ctx.work_dir / "40-candidates.json").write_text("[]")
    with pytest.raises(SystemExit, match="empty"):
        enrich.run(tmp_ctx, fetch=lambda u, t: (200, ""),
                   render=_no_render, search=_no_search)


def test_make_search_uses_websearch_and_dedupes_urls(monkeypatch):
    seen = {}

    def fake_frontier(prompt, system, schema, model, effort=None,
                      allowed_tools=None, max_turns=1):
        seen.update(prompt=prompt, tools=allowed_tools, turns=max_turns,
                    model=model)
        return {"urls": ["https://nos.nl/artikel/1", "niet-http",
                         "https://nos.nl/artikel/1",
                         "https://nu.nl/artikel/2"]}

    monkeypatch.setattr(enrich.llm, "frontier_json", fake_frontier)
    search = enrich.make_search({"model": "claude-sonnet-5", "effort": "medium"})
    # http-only + dedupe; news-only is left to the search prompt, no code filter
    assert search("Titel 1", 25, 5) == [
        "https://nos.nl/artikel/1", "https://nu.nl/artikel/2"]
    assert "Titel 1" in seen["prompt"]
    assert seen["tools"] == ["WebSearch"] and seen["turns"] > 1


def test_search_failure_is_logged_and_topic_drops(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "40-candidates.json", [_cand()])

    def search(query, timeout, max_results):
        raise enrich.llm.LlmError("no ANTHROPIC_API_KEY")

    enrich.run(tmp_ctx, fetch=lambda u, t: (403, ""),
               render=_no_render, search=search)
    log = json.loads((tmp_ctx.work_dir / "50-enrich-log.json").read_text())
    assert log["dropped_topics"] == ["Onderwerp"]
    assert "no ANTHROPIC_API_KEY" in log["topics"][0]["alt_search"]["error"]
