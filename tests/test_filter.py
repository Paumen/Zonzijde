"""S2 filter: bucket regexes (fixture titles per bucket) and batch dedupe."""

from datetime import datetime

import pytest

from zonzijde.context import TZ
from zonzijde.contracts import FeedItem, item_id
from zonzijde.stages.filter import compile_buckets, matching_buckets, split_items

# (title, buckets that must match). The negatives pin the tuned lookarounds
# from the prototype — regressions here mean a bucket was ported wrong.
BUCKET_FIXTURES = [
    # B1 — Dutch hard negative
    ("Moord in het centrum", ["B1"]),
    ("Automobilist doodgereden bij oversteekplaats", ["B1"]),
    ("Bom gevonden bij graafwerk", ["B1"]),
    ("Geweldig feest in Wijchen", []),                  # geweld(?!ig)
    ("Kramp bij marathonloper", []),                    # (?<!k)ramp
    ("Bloemencorso trekt door Batenburg", []),
    # B2 — Dutch broadly negative
    ("Drugslab opgerold in loods", ["B2"]),
    ("Ziekenhuis onder verscherpt toezicht", ["B2"]),   # ziek…enhuis
    ("Ajax verslaat PSV met ruime cijfers", []),        # (?<!ver)slaat
    ("Honderd vluchtelingen opgevangen", []),           # (?<!op)gevangen
    # B3 — English hard negative
    ("Earthquake felt across the region", ["B3"]),
    ("Skills workshop draws big crowd", []),            # (?<!\p{L})kill…
    # B4 — English broadly negative
    ("Storm damage closes bridge", ["B4"]),
    ("Brainstorm session yields ideas", []),            # (?<!\p{L})storm
    # B5 — format noise & blocked topics
    ("Trump kondigt maatregelen aan", ["B5"]),
    ("Melding via 112 leidt tot redding", ["B5"]),
    ("Feest rond 2112-jubileum", []),                   # (?<!\d)112(?!\d)
    ("Kijken naar de sterrenhemel", []),                # kijk(?!\p{L})
]


@pytest.fixture(scope="module")
def compiled(request):
    import yaml
    from tests.conftest import REPO_ROOT
    raw = yaml.safe_load((REPO_ROOT / "config" / "filters.yaml").read_text(encoding="utf-8"))
    return compile_buckets(raw["buckets"])


def test_all_buckets_compile(compiled):
    assert sorted(compiled) == ["B1", "B2", "B3", "B4", "B5"]


@pytest.mark.parametrize("title,expected", BUCKET_FIXTURES)
def test_bucket_fixtures(compiled, title, expected):
    assert matching_buckets(title, compiled) == expected


def _item(link: str, title: str = "Bloemencorso trekt door Batenburg") -> FeedItem:
    return FeedItem(
        id=item_id(link), source="gld_rvn", bron="Gld RvN", scopes=["L", "R"],
        title=title, link=link, summary="", published=None,
        fetched=datetime(2026, 7, 18, 6, 0, tzinfo=TZ))


def test_dedupe_within_batch(compiled):
    a = _item("https://example.org/artikel/1")
    b = _item("https://example.org/artikel/1?utm_source=rss")  # same canonical link
    c = _item("https://example.org/artikel/2")
    kept, rejected = split_items([a, b, c], compiled)
    assert [i.link for i in kept] == [a.link, c.link]
    assert [(r.link, r.reason) for r in rejected] == [(b.link, "duplicate")]


def test_bucket_rejection_reason_lists_all_matches(compiled):
    item = _item("https://example.org/x", title="Explosie en brand verwoesten loods")
    kept, rejected = split_items([item], compiled)
    assert kept == []
    assert rejected[0].reason == "bucket:B1,B2"


def test_duplicate_of_blocked_item_reports_duplicate(compiled):
    # The first copy claims the link even when itself bucket-blocked, exactly
    # like the prototype's seenLinks dedupe-before-filter.
    a = _item("https://example.org/x", title="Moord in het centrum")
    b = _item("https://example.org/x", title="Moord in het centrum")
    _, rejected = split_items([a, b], compiled)
    assert [r.reason for r in rejected] == ["bucket:B1", "duplicate"]
