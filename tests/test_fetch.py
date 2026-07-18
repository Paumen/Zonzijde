"""S1 fetch: feed parsing (RSS/RDF/Atom), dates, and the SRC-4 window."""

from datetime import datetime, timezone

from zonzijde.context import TZ
from zonzijde.stages.fetch import (build_rijksoverheid_url, in_window,
                                   parse_date, parse_feed, strip_html)

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Feed</title>
<item>
  <title>Nieuw wandelpad geopend</title>
  <link>https://x.nl/pad</link>
  <description><![CDATA[<p>Een &eacute;cht mooi pad.</p>]]></description>
  <pubDate>Tue, 14 Jul 2026 09:30:00 +0200</pubDate>
</item>
</channel></rss>"""

RDF = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<item rdf:about="https://dw.com/a">
  <title>Solar power milestone</title>
  <link>https://dw.com/a</link>
  <description>Record output.</description>
  <dc:date>2026-07-15T08:00:00Z</dc:date>
</item>
</rdf:RDF>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <title>Buurt plant bomen</title>
  <link rel="alternate" href="https://x.nl/bomen"/>
  <summary>Groen initiatief.</summary>
  <updated>2026-07-16T10:00:00+02:00</updated>
</entry>
</feed>"""


def test_parse_rss():
    (e,) = parse_feed(RSS)
    assert e["title"] == "Nieuw wandelpad geopend"
    assert e["link"] == "https://x.nl/pad"
    assert e["summary"] == "Een écht mooi pad."
    assert e["published"] == datetime(2026, 7, 14, 9, 30, tzinfo=TZ)


def test_parse_rdf_with_dc_date():
    (e,) = parse_feed(RDF)
    assert e["link"] == "https://dw.com/a"
    assert e["published"] == datetime(2026, 7, 15, 8, 0, tzinfo=timezone.utc)


def test_parse_atom_link_href():
    (e,) = parse_feed(ATOM)
    assert e["link"] == "https://x.nl/bomen"
    assert e["summary"] == "Groen initiatief."
    assert e["published"] is not None


def test_parse_date_variants():
    assert parse_date("Tue, 14 Jul 2026 09:30:00 +0200").hour == 9
    assert parse_date("2026-07-14T09:30:00+02:00").hour == 9
    assert parse_date("") is None
    assert parse_date("gisteren") is None


def test_strip_html():
    assert strip_html("<b>Za&nbsp;terdag</b>  markt") == "Za terdag markt"


def test_window(ctx):
    # Edition 2026-07-26, default 7-day window: start is 2026-07-19 00:00 Ams.
    assert ctx.window_start == datetime(2026, 7, 19, tzinfo=TZ)
    assert in_window(datetime(2026, 7, 20, 12, 0, tzinfo=TZ), ctx)
    assert not in_window(datetime(2026, 7, 18, 23, 59, tzinfo=TZ), ctx)
    assert in_window(None, ctx)  # undated items pass, like the prototype


def test_sources_config_loads(ctx):
    ids = [s.id for s in ctx.sources]
    assert len(ids) == len(set(ids)) == 23
    assert "gld_rvn" in ids
    # Every scope is served by at least one source (SRC-2).
    served = {sc for s in ctx.sources for sc in s.scopes}
    assert served == {"L", "R", "N", "I"}
    # Exactly one source needs a URL builder; the rest have plain URLs.
    assert [s.id for s in ctx.sources if s.builder] == ["rijksoverheid"]
    assert all(s.url for s in ctx.sources if not s.builder)


def test_rijksoverheid_url_embeds_window():
    url = build_rijksoverheid_url(datetime(2026, 7, 19, tzinfo=TZ),
                                  datetime(2026, 7, 26, 6, 0, tzinfo=TZ))
    assert url.startswith("https://www.rijksoverheid.nl/api/rss?query=")
    assert "2026-07-19" in url


def test_unimplemented_stage_fails_closed(ctx):
    import pytest
    from zonzijde.cli import run_stage
    with pytest.raises(SystemExit, match="phase 5"):
        run_stage("compose", ctx)
