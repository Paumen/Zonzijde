# De Zonzijde — Product & Editorial Specification

This document is the *what*: the rules an edition must satisfy. The *how* — components,
data contracts, orchestration — lives in [`ARCHITECTURE.md`](ARCHITECTURE.md).

The *why*, the paper's voice, and the scope definitions live in `config/prompts/brief.md`.
Language and notation conventions live in `config/prompts/stijlgids.md`.

## 1. Sourcing

- SRC-1: Items enter via RSS/Atom feeds from a configured source list; each source is
  tagged with the scopes it can serve (see `config/sources.yaml`).
- SRC-3: Deep-dive reference sources are consulted while outlining: earlier reporting by
  the same bron on the topic/person/organisation; lokaal: `www.wegwijs.nl`;
  internationaal: `www.aljazeera.com`. Regionaal and nationaal reference sources: tbd.
- SRC-4: The candidate window is the days since the previous edition.

## 2. Content pipeline

A funnel: each step narrows the stream. Normative behaviour per step; implementation in
`ARCHITECTURE.md`, prompt text in `config/prompts/`.

| ID | Fase | Rule |
|----|------|------|
| PIPE-1 | Fetch | Pull all configured feeds; a failing feed never fails the run — it is logged and skipped. |
| PIPE-2 | Fixed filter | Remove exact duplicates by link *within the fetched batch* — the same article often arrives via multiple feeds. Repeats across editions are prevented by the candidate window (SRC-4), not by historical lookback. Strip blatantly negative items and promo via the maintained regex buckets (B1–B5). |
| PIPE-3 | Score | An LLM scores each remaining item on the **direction** of the news. Scale and rules: `score.md`. |
| PIPE-4 | Select | Positively scored items go to an LLM with the brief; output is a shortlist of topics per scope, unranked, one row per source article, columns: bron, scope, titel, samenvatting, link. Counts and grouping: `select.md`. |
| PIPE-5 | Enrich | Fetch the full article text behind every selected link (two-step: plain fetch, then headless-browser render). A source row is sufficient when its title, summary, and fetched body together reach the word threshold (`config/edition.yaml` → `enrich.min_words`). |
| PIPE-6 | Outline | With brief + edition spec + shortlist: pick the stories per scope in the §5 numbers, assign length class; the picked topic carries its own sources (from PIPE-4); identify which stories carry the longer pieces; consult SRC-3 reference sources. |
| PIPE-7 | Write | Produce full Dutch article texts per the outline. see `write.md` and `stijlgids.md`. |
| PIPE-8 | Review | Copy-edit the drafts and finalise titles; see `review.md`, and `stijlgids`. |
| PIPE-9 | Editorial & compose | Consolidate into the paper: cut/shorten, final ordering, overall balance and variety; typeset into the edition PDF satisfying §6; validated against LAY/EL rules before publication. |

## 3. Edition content mix

Configured values live in `config/edition.yaml` and are templated into `outline.md`.

| ID | Requirement |
|----|-------------|
| ED-1 | Each of the four scopes contributes **at least one item, three at most**. + Four rings, strictly ordered **lokaal → regionaal → nationaal → internationaal** The rings and the places each covers are defined in `brief.md` → "Het wat".|
| ED-2 | Length mix: 1–3 longer pieces, 1–4 shorter ones, 2–5 of standard length. |
| ED-3 | Every article carries a head, a location, and the publication date of its most recent source article. Location and date are set at compose (PIPE-9), not by the writer. |
| ED-5 | Edition body text totals ≈ 2,800–3,400 words. |
| ED-6 | Vary article forms across the edition — not all aphoristic kickers; at least
  one piece somewhat funnier/more ironic; use devices like an analogy or METAPHOR. |
  
## 4. Layout & typography

| ID | Requirement |
|----|-------------|
| LAY-1 | The edition fills **3.5–4 A4 pages**, three columns, 12 mm margins all round, 6 mm column gap. |
| LAY-2 | Body text: 9.5 pt on 11 pt line height. |
| LAY-3 | No line consists of a single word. |
| LAY-4 | No column runs three lines or fewer. |
| LAY-5 | No stretch of white space grows taller than three lines. |
| LAY-7 | The printed edition is 4 A4 pages, imposed as an A3 booklet: two A3 landscape sheets (420×297 mm), outer sheet pages 4\|1, inner sheet pages 2\|3 — fold once to an A4 booklet. Content fills 3.5–4 pages (LAY-1). |

## 5. Fixed elements

Appearance of the hand-drawn elements is described in `brief.md`; the illustration's
style rules live in `illustrate.md`. This section fixes only presence and placement.

| ID | Requirement |
|----|-------------|
| EL-1 | Masthead with the sunflower, top of page 1. |
| EL-2 | Weather strip after the lokaal news, typically landing on page 2 (Wijchen; today + 5 days; max/min temperature and precipitation chance; source Open-Meteo). |
| EL-3 | One or two custom illustration per edition, drawn anew for that edition's article. Set with an article, preferably on page 2 or 3, usually regional or national; one column wide. |
| EL-4 | The edition closes with the landscape at the bottom of the last page. |

## 6. Cadence, delivery & operations

| ID | Requirement |
|----|-------------|
| OPS-1 | Cadence: weekly, edition dated Sunday. |
| OPS-2 | Delivery: the deliverable is a **print-ready PDF in A3 booklet imposition** (LAY-7), typeset directly from the edition data. |
| OPS-4 | Every run produces an inspectable trail: per-fase artifacts, a funnel report (counts in/out per fase), sources used, stories dropped or re-sourced, and LLM cost. |
