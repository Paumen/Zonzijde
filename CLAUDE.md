# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

De Zonzijde is a weekly, printable Dutch newspaper of genuinely good news for
Gemeente Wijchen and outward (lokaal → regionaal → nationaal → internationaal).
The deliverable is a print-ready PDF (A3 booklet imposition); GitHub Pages serves
the archive. There is no HTML edition.

**The two documents that govern all work here:**

- `docs/SPEC.md` — the *what*: editorial and layout rules an edition must satisfy.
  Requirement IDs (`BR-1`, `GEO-2`, `PIPE-5`, `ED-3`, `LAY-7`, `EL-2`, `OPS-5`, `OQ-1`, …)
  are stable — reference them in code, prompts, tests, and PRs. Anything genuinely
  undecided is an Open Question (§9), never silently resolved.
- `docs/ARCHITECTURE.md` — the *how*: the S1–S9 pipeline design, data contracts,
  target repo layout (`zonzijde/` Python package), Typst typesetting, orchestration,
  and the phased build order (§11). New implementation work should follow that plan.

The original concept is archived at `docs/history/concept_ZZ.md`; SPEC.md supersedes it.

## Current state: pipeline through S5, prototypes for the rest

The `zonzijde/` package exists through **build phase 3** (ARCHITECTURE §11):
S1 fetch, S2 filter, S3 score (Gemini light tier, fail-closed), S4 select
(frontier tier via the Claude Agent SDK) and S5 enrich (two-stage full-text
fetch, re-source-or-drop) run as `python -m zonzijde …`, with config in
`config/` and the scorer eval in `tests/eval_score.py`. Still manual:

- `tools/fetch-articles.py` — standalone full-text fetcher, now absorbed into
  the pipeline as stage S5 (`zonzijde/stages/enrich.py`); the tool stays for
  manual/debug use on ad-hoc URL lists.
- `proto_krant.html` — hand-built edition; the design reference for the future Typst
  template. `proto_index.html` is superseded, kept for reference.
- `proto_fetchfilter.html` — the original browser app; remains as a manual
  inspection/debug UI now that its sources, buckets and scoring live in the pipeline.

When migrating prototype logic into the pipeline, prefer porting over rewriting —
the regex buckets, source list, and scoring behaviour are tuned.

## Commands

```bash
# The pipeline (run from repo root; deps: pip install -e ".[dev]")
python3 -m zonzijde run --edition YYYY-MM-DD --until filter   # S1+S2, no keys needed
python3 -m zonzijde score --edition YYYY-MM-DD                # S3, needs GEMINI_API_KEY
python3 -m zonzijde select --edition YYYY-MM-DD               # S4, needs ANTHROPIC_API_KEY
python3 -m zonzijde enrich --edition YYYY-MM-DD               # S5; ANTHROPIC_API_KEY only
                                                              # for blocked-topic re-search
# S5 browser fallback for blocked links (optional):
#   pip install -e ".[browser]" && playwright install chromium
# Artifacts land in editions/<date>/work/, report in editions/<date>/report.md
# --from/--until resume a slice against existing artifacts (ARCHITECTURE §3)

# Tests (no network, no keys)
python3 -m pytest

# Scorer eval (live Gemini; re-run + post numbers on any change to
# prompts/score.md, the light model, or the buckets — ARCHITECTURE §9)
GEMINI_API_KEY=... python3 tests/eval_score.py

# Fetch full article text for selected links (run from repo root)
# Input: the MD table copied from proto_fetchfilter.html, or bare URLs
python3 tools/fetch-articles.py table.md          # or URLs / stdin
# Deps: pip install requests trafilatura
# Optional (browser fallback): pip install playwright && playwright install chromium
# Output: articles.md + articles.json in repo root (gitignored)
# Flags: --no-browser --concurrency N --min-words N --timeout S

# Regenerate self-hosted font subsets (fonts/*.woff2 + fonts.css)
python3 tools/build-fonts.py                      # deps: fonttools, brotli
```

The prototypes are opened directly in a browser; no dev server.

## Conventions and hard rules

- **Content is Dutch** (BR-6); docs, code, and commit messages are English. Domain
  terms stay Dutch: bron, scope, titel, samenvatting, lokaal/regionaal/nationaal/
  internationaal, krant.
- **Prompts are versioned files** in `config/prompts/` (brief, score, select, outline,
  write) with a YAML version header. They are canonical — the wording in
  `proto_fetchfilter.html` is legacy. Changing a prompt means bumping its version;
  changes to `score.md` must re-run the scorer eval once it exists (ARCHITECTURE §9).
- **No API keys in the repo or client HTML** (OPS-5). Keys live in Actions secrets /
  local env only. (Historical violation in `proto_fetchfilter.html` — see
  ARCHITECTURE §10; don't repeat it.)
- **No summary fallback** (PIPE-5): an RSS blurb is never writing material. Blocked
  stories are re-sourced or dropped and logged — stage S5 (`enrich.py`) implements
  exactly this. Note: the standalone `tools/fetch-articles.py` still falls back to
  the RSS `samenvatting` for its manual/debug use; never port that behaviour into
  the pipeline (ARCHITECTURE §1).
- **Fail-closed scoring** (PIPE-3/S3): unscored items never advance.
- **Typography**: Fraunces (heads), Newsreader (body), Archivo (labels) — self-hosted
  static instances in `fonts/`, generated by `tools/build-fonts.py`. Never link Google
  Fonts at runtime; variable fonts break PDF embedding (that's why the static
  instances exist).
- **Human editorial gate** (OPS-3/OQ-5): nothing auto-publishes. The edition PR is the
  gate; merge = publish via `.github/workflows/pages.yml`.
- LAY-3/4/5 (no single-word lines, no ≤3-line columns, no >3-line whitespace holes)
  are hard gates: violating editions get re-composed, not shipped.
