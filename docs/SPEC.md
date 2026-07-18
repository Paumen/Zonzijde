# De Zonzijde — Product & Editorial Specification

Status: **draft v1** — distilled from the original concept (archived at
`docs/history/concept_ZZ.md`) and the working prototypes
(`proto_fetchfilter.html`, `proto_index.html`, `proto_krant.html`, `tools/fetch-articles.py`).
This document is the *what*: the rules an edition must satisfy. The *how* — components,
data contracts, orchestration — lives in [`ARCHITECTURE.md`](ARCHITECTURE.md).

Requirement IDs (`ED-3`, `LAY-2`, …) are stable and may be referenced from code,
prompts, tests, and PRs. Anything genuinely undecided is listed in §9 Open questions,
not silently resolved.

---

## 1. Product brief

People are worn out by negative news. It pours in non-stop through every channel, and
on many fronts life is measurably better than ten, twenty, thirty years ago — yet people
don't feel it, see it, or believe it. De Zonzijde is the counterweight: a calm, weekly,
printable newspaper of genuinely good news, built outward in rings — local first, then
regional, national, global.

It is **relief, not filler**: no forced feel-good pieces, no promo, no repackaged hype.
Local news is the heart — tangible ("you could walk over and verify it yourself"),
trustworthy, and something no other channel gives you. Bigger news appears only when
there is a genuinely different angle: a clear zoom-out on a topic, or a zoom-in on a
specific part of it. Fifteen minutes of reading to start the morning; on a day with more
time or a story that catches you, the longer pieces are there.

### Product invariants

| ID | Requirement |
|----|-------------|
| BR-1 | Every story is genuinely good or positive news — never neutral news dressed up, never forced feel-good filler. |
| BR-2 | Smaller local stories are not "filler" when the reader has a connection to them; the bar for lokaal is relevance + positivity, not magnitude. |
| BR-3 | Generic coverage of major/hyped news is excluded — it reaches people anyway. Exception: a distinctly different perspective (zoom-out or zoom-in). |
| BR-4 | Promo, marketing, and product-driven items never appear. |
| BR-5 | The paper is calm in tone and presentation: no sensationalism, no clickbait mechanics, black-and-white, print-first. |
| BR-6 | The edition is in Dutch. |

## 2. Geographic scopes

Four rings, strictly ordered **lokaal → regionaal → nationaal → internationaal**
throughout the edition (GEO-1).

| Scope | Coverage |
|-------|----------|
| **Lokaal** | Gemeente Wijchen: Wijchen, Alverna, Balgoij, Batenburg, Bergharen, Hernen, Laak, Leur, Niftrik, Woezik. Landmarks: De Berendonck, De Groene Heuvels, Loonse Waard, Wijchens Meer, Wijchens Ven, Bijsterhuizen. |
| **Regionaal** | Villages and cities around Wijchen: Beuningen, Druten, Heumen (Malden, Overasselt, Nederasselt), Grave, Land van Cuijk, Nijmegen; Groene Metropoolregio Arnhem-Nijmegen, Rijk van Nijmegen, Land van Maas en Waal, Zuid-Gelderland, Gelderland. De Maas, de Waal, Overasseltse en Hatertse Vennen, Heumensoord. |
| **Nationaal** | The provinces, Nederland, Waddeneilanden, Nederlandse Antillen, Vlaanderen, German border region (NRW). De Veluwe, Waddenzee, Noordzee, Rijn, Maas, Waal, Schelde, IJsselmeer, Markermeer. |
| **Internationaal** | Neighbouring countries, Europe, continents, countries. Oceans, major seas. |

- GEO-2: A story belongs to the innermost ring it plausibly fits; a Nijmegen story is
  regionaal even if a national outlet carried it.
- GEO-3: Any scope's story may stretch into a longer, in-depth piece when the topic
  deserves the space.

## 3. Sourcing

- SRC-1: Items enter via RSS/Atom feeds from a configured source list; each source is
  tagged with the scopes it can serve (see `config/sources.yaml` in the target layout;
  the current list lives in `proto_fetchfilter.html`).
- SRC-2: The source list must cover all four scopes every edition.
- SRC-3: Deep-dive reference sources are consulted while outlining (`config/prompts/outline.md`):
  earlier reporting by the same bron on the topic/person/organisation; lokaal:
  `www.wegwijs.nl`; internationaal: `www.aljazeera.com`. Regionaal and nationaal
  reference sources: **open** (OQ-1).
- SRC-4: The candidate window is the days since the previous edition (default 7 days);
  it may be widened for lokaal when the local harvest is thin.

## 4. Content pipeline (functional stages)

A funnel: each step narrows the stream. Normative behaviour per step; implementation in
`ARCHITECTURE.md`.

| ID | Stage | Rule |
|----|-------|------|
| PIPE-1 | Fetch | Pull all configured feeds; a failing feed never fails the run — it is logged and skipped. |
| PIPE-2 | Fixed filter | Remove exact duplicates by link *within the fetched batch* — the same article often arrives via multiple feeds (e.g. NOS algemeen and NOS economie). Repeats across editions are prevented by the candidate window (SRC-4), not by historical lookback. Strip blatantly negative items and promo via the maintained regex buckets (B1–B5). Deliberate double filter with PIPE-3's promo cap. |
| PIPE-3 | Score | A lightweight LLM scores each remaining item −2…+2 on the **direction** of the news only — not size or reach. Promo/marketing/product items cap at 0. The canonical scoring prompt is versioned in `config/prompts/`. |
| PIPE-4 | Select | Items scoring +1/+2 go to a frontier LLM with the brief; output is a ranked top-5 of *topics* per scope, one row per source article (a topic covered by multiple sources gets multiple rows), columns: bron, scope, titel, samenvatting, link. |
| PIPE-5 | Enrich | Fetch the full article text behind every selected link (two-stage: plain fetch, then headless-browser render). **No summary fallback**: a short RSS blurb is never writing material (WR-2). If a link stays blocked, the topic's other source articles stand in (the candidate table lists one row per source). A topic with no usable full text on any of its rows is dropped and logged in the run report. Enrichment is plain code — no model call. |
| PIPE-6 | Outline | With brief + edition spec + full texts: pick the stories per scope in the §5 numbers, assign length class, article type, tone/angle, and sources per story; front page led by the best lokaal story; identify which stories carry the longer pieces; consult SRC-3 reference sources. |
| PIPE-7 | Write | Produce full Dutch article texts per the outline. Never refer to accompanying images/illustrations; never refer to De Zonzijde itself, "deze krant", its intent, or why a story is included. |
| PIPE-8 | Review | Fact-check against the fetched source texts, correct grammar/spelling, finalise titles. |
| PIPE-9 | Editorial & compose | Consolidate into the paper: cut/shorten, final ordering, overall balance and variety; typeset into the edition PDF satisfying §6; validated against LAY/EL rules before publication. |

Writing-variety rules (apply across PIPE-6..9):

- WR-1: Vary article forms across the edition — not all aphoristic kickers; at least
  one piece somewhat funnier/more ironic; use devices like an analogy or metaphor; one
  piece may refer to another article in the same edition.
- WR-2: Every article is grounded in its fetched source text(s); no invented facts,
  names, numbers, or quotes (enforced by PIPE-8).

## 5. Edition content mix

| ID | Requirement |
|----|-------------|
| ED-1 | Each of the four scopes contributes **two items, three at most**. |
| ED-2 | Length mix: 2–3 longer pieces, 2–3 shorter ones, 3–5 of standard length. |
| ED-3 | Every article carries a title, a location, and the publication date of its source article. When a story draws on several sources, the date shown is the **most recent** source's publication date. |
| ED-4 | An article typically runs 3–11 paragraphs. |
| ED-5 | Edition body text totals ≈ 2,800–3,400 words — about fifteen minutes of reading. |
| ED-6 | Ring order lokaal → regionaal → nationaal → internationaal is strict throughout (GEO-1); the front page leads with the best lokaal story. |

## 6. Layout & typography

| ID | Requirement |
|----|-------------|
| LAY-1 | The edition fills **3.5–4 A4 pages**, three columns, 12 mm margins all round, 6 mm column gap. |
| LAY-2 | Body text: 9.5 pt on 11 pt line height. |
| LAY-3 | No line consists of a single word. |
| LAY-4 | No column runs three lines or fewer. |
| LAY-5 | No stretch of white space grows taller than three lines. |
| LAY-6 | Typography per the established prototype: Fraunces (heads), Newsreader (body), Archivo (labels/meta) — self-hosted font files embedded in the PDF, no runtime font dependencies. |
| LAY-7 | The printed edition is exactly **4 A4 pages**, imposed as an A3 booklet: two A3 landscape sheets (420×297 mm), outer sheet pages 4\|1, inner sheet pages 2\|3 — fold once to an A4 booklet. Content fills 3.5–4 pages (LAY-1); the closing landscape (EL-4) absorbs the slack on page 4. |

LAY-3..5 are hard gates: an edition that violates them is re-composed (cut/shorten/reflow),
not published as-is.

## 7. Fixed & optional elements

| ID | Requirement |
|----|-------------|
| EL-1 | Masthead: the paper's title with the hand-drawn sunflower in front of it. |
| EL-2 | Weather strip directly after the lokaal news, typically landing on page 2 (Wijchen; today + 5 days; max/min temperature and precipitation chance; source Open-Meteo). |
| EL-3 | One custom illustration per edition, **drawn anew for that edition's article** — never picked from a stock set. Set with an article, preferably on page 3 or 4, usually regional or national. Hand-drawn style, one column wide, fits the Zonzijde theme and/or the article's topic; no colour — minimalist fine lines, patterns, strokes. |
| EL-4 | The edition closes with the hand-drawn landscape at the bottom of the last page — flowers, a village in the distance, and a sun. |
| EL-5 | Optional per edition: a quote, a number of the week, or a side story set in a light grey block. |
| EL-6 | Articles never reference the illustrations, and illustrations carry no colour (BR-5). |

## 8. Cadence, delivery & operations

| ID | Requirement |
|----|-------------|
| OPS-1 | Cadence: weekly, edition dated Sunday (matches editions of 28 juni, 12 juli, 19 juli 2026). Confirmation: OQ-3. |
| OPS-2 | Delivery: the deliverable is a **print-ready PDF in A3 booklet imposition** (LAY-7), as with the editions produced to date, typeset directly from the edition data — there is no HTML edition. The PDF archive is served via GitHub Pages. |
| OPS-3 | A human editorial gate reviews each edition before publication (see ARCHITECTURE §7); the pipeline must make that review cheap: full provenance from every article back to its sources. |
| OPS-4 | Every run produces an inspectable trail: per-stage artifacts, a funnel report (counts in/out per stage), sources used, stories dropped or re-sourced, and LLM cost. |
| OPS-5 | All API keys are server-side secrets. No key ships in client HTML or the repo. (The Gemini key currently embedded in `proto_fetchfilter.html` must be rotated and moved — see ARCHITECTURE §10.) |

## 9. Open questions

| ID | Question | Current stance |
|----|----------|----------------|
| OQ-1 | Regionaal and nationaal deep-dive reference sources ([TODO] in `config/prompts/outline.md`). | Outline stage consults only same-bron history until decided. |
| OQ-2 | ~~Illustration sourcing~~ **Resolved**: each edition's illustration is a custom drawing for that edition — not picked from a library of generic illustrations. The pipeline draws a new SVG in the house style per edition; the editor judges it at the gate and can redraw or replace it. |
| OQ-3 | Cadence: weekly Sunday is inferred from the three existing editions, not stated in the concept. | Weekly Sunday assumed. |
| OQ-4 | Attribution policy: articles are rewritten from source reporting — is a source credit line (bron) printed per article beyond ED-3's date+location? | Provenance is kept in the edition manifest either way; print attribution undecided. |
| OQ-5 | May the pipeline ever auto-publish without the human gate (OPS-3)? | No — gate stays until trust is established. |
| OQ-6 | Distribution beyond Pages (e-mail, print run)? | Out of scope for v1. |
