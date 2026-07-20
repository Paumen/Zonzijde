# De Zonzijde — Product & Editorial Specification

This document is the *what*: the rules an edition must satisfy. The *how* — components,
data contracts, orchestration — lives in [`ARCHITECTURE.md`](ARCHITECTURE.md).

The *why* lives in config/prompts/brief.md

## 1. Geographic scopes

Four rings, strictly ordered **lokaal → regionaal → nationaal → internationaal**
throughout the edition (GEO-1).

| Scope | Coverage |
|-------|----------|
| **Lokaal** | Gemeente Wijchen: Wijchen, Alverna, Balgoij, Batenburg, Bergharen, Hernen, Laak, Leur, Niftrik, Woezik. Landmarks: De Berendonck, De Groene Heuvels, Loonse Waard, Wijchens Meer, Wijchens Ven, Bijsterhuizen. |
| **Regionaal** | Villages and cities around Wijchen: Beuningen, Druten, Heumen (Malden, Overasselt, Nederasselt), Grave, Land van Cuijk, Nijmegen; Groene Metropoolregio Arnhem-Nijmegen, Rijk van Nijmegen, Land van Maas en Waal, Zuid-Gelderland, Gelderland. De Maas, de Waal, Overasseltse en Hatertse Vennen, Heumensoord. |
| **Nationaal** | The provinces, Nederland, Waddeneilanden, Nederlandse Antillen, Vlaanderen, German border region (NRW). De Veluwe, Waddenzee, Noordzee, Rijn, Maas, Waal, Schelde, IJsselmeer, Markermeer. |
| **Internationaal** | Neighbouring countries, Europe, continents, countries. Oceans, major seas. |

- GEO-2: Any scope's story may stretch into a longer, in-depth piece when the topic
  deserves the space.

## 2. Sourcing

- SRC-1: Items enter via RSS/Atom feeds from a configured source list; each source is
  tagged with the scopes it can serve (see `config/sources.yaml`.
- SRC-2: The source list must cover all four scopes every edition.
- SRC-3: Deep-dive reference sources are consulted while outlining (`config/prompts/outline.md`):
  earlier reporting by the same bron on the topic/person/organisation; lokaal:
  `www.wegwijs.nl`; internationaal: `www.aljazeera.com`. Regionaal and nationaal
  reference sources: tbd.
- SRC-4: The candidate window is the days since the previous edition (default 7 days).

## 4. Content pipeline (functional stages)

A funnel: each step narrows the stream. Normative behaviour per step; implementation in
`ARCHITECTURE.md`.

| ID | Stage | Rule |
|----|-------|------|
| PIPE-1 | Fetch | Pull all configured feeds; a failing feed never fails the run — it is logged and skipped. |
| PIPE-2 | Fixed filter | Remove exact duplicates by link *within the fetched batch* — the same article often arrives via multiple feeds (e.g. NOS algemeen and NOS economie). Repeats across editions are prevented by the candidate window (SRC-4), not by historical lookback. Strip blatantly negative items and promo via the maintained regex buckets (B1–B5). Deliberate double filter with PIPE-3's promo cap. |
| PIPE-3 | Score | A LLM scores each remaining item −2…+2 on the **direction** of the news only — not size or reach. Promo/marketing/product items cap at 0. The canonical scoring prompt is versioned in `config/prompts/`. |
| PIPE-4 | Select | Items scoring +1/+2 go to an LLM with the brief; output is 7 *topics* per scope for lokaal/regionaal and 5 for nationaal/internationaal (unranked), one row per source article (a topic covered by multiple sources gets multiple rows), columns: bron, scope, titel, samenvatting, link. |
| PIPE-5 | Enrich | Fetch the full article text behind every selected link (two-stage: plain fetch, then headless-browser render). A source row is sufficient when its title, summary, and fetched body together reach the word threshold (`config/edition.yaml` → `enrich.min_words`); a row below it is not writing material (WR-2). If a link stays blocked, the topic's other source articles stand in (the candidate table lists one row per source). A topic with no sufficient row is dropped. |
| PIPE-6 | Outline | With brief + edition spec + shortlist: pick the stories per scope in the §5 numbers, assign length class; the picked topic carries its own sources (from PIPE-4); front page led by the best lokaal story; identify which stories carry the longer pieces; consult SRC-3 reference sources. |
| PIPE-7 | Write | Produce full Dutch article texts per the outline. Never refer to accompanying images/illustrations; never refer to De Zonzijde itself, "deze krant", its intent, or why a story is included. |
| PIPE-8 | Review | Copy-edit the drafts: correct Dutch grammar/spelling/phrasing, finalise titles. |
| PIPE-9 | Editorial & compose | Consolidate into the paper: cut/shorten, final ordering, overall balance and variety; typeset into the edition PDF satisfying §6; validated against LAY/EL rules before publication. |

Writing-variety rules (apply across PIPE-6..9):

- WR-1: Vary article forms across the edition — not all aphoristic kickers; at least
  one piece somewhat funnier/more ironic; use devices like an analogy or metaphor.
- WR-2: Every article is grounded in its source material (title, summary, and fetched
  body); no invented facts, names, numbers, or quotes (grounded at PIPE-7 write; the
  human editorial gate is the fact-check).

## 5. Edition content mix

| ID | Requirement |
|----|-------------|
| ED-1 | Each of the four scopes contributes **at least one item, three at most**. |
| ED-2 | Length mix: 1–3 longer pieces, 1–3 shorter ones, 2–5 of standard length. |
| ED-3 | Every article carries a head, a location, and the publication date of its source article. When a story draws on several sources, the date shown is the **most recent** source's publication date. |
| ED-5 | Edition body text totals ≈ 2,800–3,400 words — about fifteen minutes of reading. |

## 6. Layout & typography

| ID | Requirement |
|----|-------------|
| LAY-1 | The edition fills **3.5–4 A4 pages**, three columns, 12 mm margins all round, 6 mm column gap. |
| LAY-2 | Body text: 9.5 pt on 11 pt line height. |
| LAY-3 | No line consists of a single word. |
| LAY-4 | No column runs three lines or fewer. |
| LAY-5 | No stretch of white space grows taller than three lines. |
| LAY-7 | The printed edition is **4 A4 pages**, imposed as an A3 booklet: two A3 landscape sheets (420×297 mm), outer sheet pages 4\|1, inner sheet pages 2\|3 — fold once to an A4 booklet. Content fills 3.5–4 pages (LAY-1); the closing landscape (EL-4) absorbs the slack on page 4. |

## 7. Fixed elements

| ID | Requirement |
|----|-------------|
| EL-1 | Masthead: the paper's title with the hand-drawn sunflower in front of it. |
| EL-2 | Weather strip directly after the lokaal news, typically landing on page 2 (Wijchen; today + 5 days; max/min temperature and precipitation chance; source Open-Meteo). |
| EL-3 | One custom illustration per edition, **drawn anew for that edition's article** — never picked from a stock set. Set with an article, preferably on page 3 or 4, usually regional or national. Hand-drawn style, one column wide, fits the Zonzijde theme and/or the article's topic; no colour — minimalist fine lines, patterns, strokes. |
| EL-4 | The edition closes with the hand-drawn landscape at the bottom of the last page — flowers, a village in the distance, and a sun. |

## 8. Cadence, delivery & operations

| ID | Requirement |
|----|-------------|
| OPS-1 | Cadence: weekly, edition dated Sunday (matches editions of 28 juni, 12 juli, 19 juli 2026). |
| OPS-2 | Delivery: the deliverable is a **print-ready PDF in A3 booklet imposition** (LAY-7), as with the editions produced to date, typeset directly from the edition data. |
| OPS-4 | Every run produces an inspectable trail: per-stage artifacts, a funnel report (counts in/out per stage), sources used, stories dropped or re-sourced, and LLM cost. |

