# De Zonzijde — System Design

Status: **draft v1** — companion to [`SPEC.md`](SPEC.md) (the *what*). This is the *how*:
a coherent automation pipeline, a weekly,
reviewable, mostly-automated production system.

---

## 1. Where we're going

Target: one command — `python -m zonzijde run --edition 2026-07-26` — executes the whole
funnel and opens an edition PR; a human reviews and merges; Pages publishes.

## 2. Design principles

1. **Staged artifacts, not a monolith.** Every stage reads one JSON artifact and writes
   the next. Any stage can be re-run in isolation; a failed run resumes from the last
   good artifact. This is also what makes the editorial gate (OPS-3) cheap: everything
   is inspectable and diffable in the PR.
2. **Cheap-first LLM funnel.** Volume work (scoring ~1–2k items/week) runs on Haiku;
   the Sonnet/Opus calls only happen after the stream has narrowed to dozens
   (select) and then ~10–15 stories (outline/write/review).
3. **Deterministic frame, creative core.** Fetching, filtering, dedupe, layout, and
   validation are plain code. LLMs do only what code can't: judge direction, select,
   outline, write, review. Every LLM step has a versioned prompt and a schema-validated
   output.
4. **The data is the source of truth; the PDF is the product.** `edition.json` holds
   the finished edition; the booklet PDF is a deterministic rendering of it. There is
   no HTML edition. Weather and all content are baked at compose time; the published
   artifact has no runtime dependencies and no keys (OPS-5).
5. **Human gate before the world sees it.** The pipeline proposes; the editor disposes
   (merge = publish). Nothing in the design assumes unattended publication.

## 3. Pipeline stages

```mermaid
flowchart TD
    subgraph gather [Gather - plain code]
        S1[S1 fetch\nRSS/Atom pull] --> S2[S2 filter\ndedupe + regex buckets]
    end
    subgraph judge [Judge - cheap LLM]
        S3[S3 score\ndirection -2..+2]
    end
    subgraph curate [Curate - LLM]
        S4[S4 select\ntop-5 topics per scope]
        S5[S5 enrich\nfull article text]
        S6[S6 outline\nedition plan]
    end
    subgraph produce [Produce - LLM + code]
        S7[S7 write\nDutch articles]
        S8[S8 review\ncopy-edit, language, titles]
        S9[S9 compose\nTypst render + booklet PDF]
    end
    S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9
    S9 --> PR[Edition PR\nhuman editorial gate]
    PR -->|merge| Pages[GitHub Pages]
    W[Open-Meteo weather] --> S9
    A[custom SVG drawing\nper edition] --> S9
```

| Stage | Spec | Kind | Input → output artifact | Notes |
|-------|------|------|--------------------------|-------|
| S1 `fetch` | PIPE-1 | code | `config/sources.yaml` → `10-items.json` | Concurrent pull with timeout; per-feed failures logged in the run report, never fatal. Window per SRC-4. |
| S2 `filter` | PIPE-2 | code | `10` → `20-filtered.json` + `20-rejected.json` | Batch dedupe + bucket filtering per PIPE-2; buckets B1–B5 live in `config/filters.yaml`. Rejections keep their reason for auditability. |
| S3 `score` | PIPE-3 | LLM | `20` → `30-scored.json` | Batched (~80 items/call, concurrent), schema-enforced output, prompt `prompts/score.md`. Unparseable batch → items left unscored and excluded (fail-closed: unscored never advances). |
| S4 `select` | PIPE-4 | LLM | `30` (+1/+2 only) → `40-candidates.json` | Inputs `prompts/brief.md` + `prompts/select.md` + scored titles/summaries; output shape per PIPE-4. |
| S5 `enrich` | PIPE-5 | code (+LLM) | `40` → `50-articles.json` | `tools/fetch-articles.py` refactored into the package; two-stage fetch (requests, then headless browser). Re-source-or-drop per PIPE-5: the topic's sibling rows in `40-candidates.json` are the only re-source; a topic with no full text is dropped and logged. Each full-text article's in-body links are classified by the model (EXT/INT/NAV/PROMO); EXT+INT links (denylist-filtered, capped) are followed as best-effort background `references` — never gating a topic's drop status. |
| S6 `outline` | PIPE-6 | LLM | `40` + `50` (ok flags) + SPEC §5 → `60-outline.json` | A quick pitch: produces the edition plan per PIPE-6 (story picks, length classes) from the **shortlist** — titles + RSS summaries, not the full texts. One plain call, no tools, no browsing; the writers (S7) get the texts. The model's editorial choices (ED-1 counts, ED-2 mix, which topics) are taken as-is and judged at the human gate — not validated in code. Code still assembles what it owns: `pos` and the lokaal front by ring-order sort (ED-6), and `source_date` (ED-3, the *newest* source's date). SRC-3 reference reading is not automated here (OQ-1). |
| S7 `write` | PIPE-7 | LLM | `60` → `70-drafts.json` | One call per article (grounded on its S5 texts only); the rules from PIPE-7 (length guidance, no self-reference) are in the system prompt and not re-checked in code. `words` computed. |
| S8 `review` | PIPE-8 | LLM | `70` → `80-reviewed.json` | Per article, copy-edited in isolation (draft text only — no source or reference text): Dutch grammar/spelling/phrasing and title, emitting a correction log for the PR. Output taken as-is, not validated in code. |
| S9 `compose` | PIPE-9 | code (+LLM illustration) | `80` → `editions/<date>/krant-A3boekje.pdf` + `edition.json` | Custom-illustration drawing, Typst render, weather baking, typeset checks, booklet imposition — all per §5. The only LLM step is the illustration; layout violations the reflow knob can't fix fail to the editorial gate. |

Stage contract: every stage is `python -m zonzijde <stage> --edition YYYY-MM-DD`;
`run` chains them; `--from/--until` re-run a slice against existing artifacts.

## 4. Data contracts

Artifacts live in `editions/<date>/work/`, are pretty-printed JSON (stable key order —
diffable in the PR), and validate against pydantic models in `zonzijde/contracts.py`.
Item identity: `id = sha1(canonical_link)[:12]`, assigned at S1 and carried through, so
every printed article traces back to its feed items.

## 5. Compose: Typst typesetting, checks & booklet imposition

**Engine choice: Typst, not a browser.** 
typesets like LaTeX (whole-paragraph line-break optimisation, real widow/orphan
control, Dutch hyphenation), outputs PDF directly, is deterministic when pinned to a
version, and its templates are plain text that both humans and LLMs edit well. The
LAY rules go from "detect and repair" to mostly "cannot occur".

`templates/krant.typ` — the
A4 three-column grid, 12 mm margins, 6 mm gutters, 9.5/11 pt body (LAY-1/2), Fraunces /
Newsreader / Archivo, masthead, kickers, weather strip — and renders `edition.json`
straight to a 4-page A4 PDF.

**Typeset checks.** Compile, then verify LAY-1..5 and LAY-7 against the compiled
layout (Typst's introspection/query where possible, PDF text extraction otherwise).
Violations should be rare — LAY-3 is prevented in the template rather than repaired.
The only automatic remedy is the reflow knob (moving the illustration slot to the
next eligible article) — max 3 recompiles; anything still violating fails the run
with the violation report, and the editorial gate resolves it (edit the copy or
reflow, then re-run). The target is **exactly 4 A4 pages**, closing landscape
absorbing the slack (LAY-7).

**Booklet imposition.** pypdf imposes the 4 A4 pages onto the two A3 sheets in LAY-7's
order, producing the fold-ready `krant-A3boekje.pdf` — the deliverable (OPS-2).

Weather (EL-2) is fetched from Open-Meteo at compose time and baked into
`edition.json`, so the rendered edition is a closed artifact (principle 4).

**Illustration (EL-3): drawn anew every edition.** S9 has the model pick a subject and draw a fresh one-column SVG in the house style — black-and-white, minimalist fine lines,
patterns, strokes. The style
lives in `prompts/illustrate.md` together with two or three reference drawings from
past editions (references teach the *style*, they are never reused as the drawing).
Saved as `work/85-illustration.svg`, referenced from `edition.json`, and judged by the
editor at the gate like any article: redraw or replace before merge. Only the masthead
sunflower and the closing landscape (EL-1/EL-4) are fixed assets.

## 6. LLM usage & budget

| Stage | Model | Calls/edition | Tokens (rough) | Failure policy |
|-------|-------|---------------|----------------|----------------|
| S3 score | Claude Haiku | ~15–25 batches | ~150k in / 5k out | no retry; unscored = excluded (fail-closed) |
| S5 classify | Claude Haiku | ~10–15 (per article) | small | best-effort |
| S4 select | Claude Sonnet | 1 | ~30k in / 2k out | no retry; fatal on failure or invalid output |
| S6 outline | Claude Opus | 1 | ~8k in / 3k out | idem |
| S7 write | Claude Sonnet | ~10–12 (per article) | ~6k in / 1k out each | no retry; a failed article fails the run |
| S8 review | Claude Sonnet | ~10–12 | ~5k in / 1k out each | idem |
| S9 illustration | Claude Sonnet | 1 | ~5k in / 5k out | reads brief + views/reads the two house drawings (Read tool), then draws; invalid SVG surfaces at the gate |

Order of magnitude: a few dollars per edition, dominated by S6–S8. Every response that
feeds a later stage is JSON-schema-validated at the call layer; an invalid response is
not retried — the stage excludes the item (S3) or fails the run (S4+).
Prompts are files in `config/prompts/` with a version header; `edition.json` records the
versions used, so output changes are attributable to prompt changes.

Provider access goes through a thin adapter (`zonzijde/llm.py`); each stage's model is
configured per stage under `llm.stages` in `config/edition.yaml` — swappable without
touching stages. **Every stage is driven through the Claude Agent SDK, not raw API
calls**: each stage invocation is a short agent session, which gives S9's illustration
step file context (the Read tool, to view and read the house-style drawings) and
provides schema-enforced structured output out of the box. The
curation and writing stages (S4, S6, S7, S8) are single prompt-in/JSON-out calls with
no tools; S5 enrichment is plain code apart from one Haiku call per article that
classifies its in-body links. S3 scoring and S5 link classification run the same
sessions on Haiku — single prompt, no tools — so one auth path covers the whole
pipeline.

## 7. Orchestration

**GitHub Actions, two workflows:**

1. `edition.yml` — cron early Sunday morning (Europe/Amsterdam) + `workflow_dispatch`
   (inputs: `edition_date`, `from_stage` for resume). Steps: checkout → install
   (Python deps, **Playwright Chromium with its system libraries** — `playwright
   install --with-deps chromium`, needed by S5's browser-render fetch; the Typst
   compiler for S9 comes in as the `typst` Python package, version-pinned in
   `pyproject.toml`) → `python -m zonzijde run` → commit
   `editions/<date>/` to branch `edition/<date>` → open the **edition PR**.
2. `pages.yml` (existing) — on merge to `main`, deploy. Extended to (re)generate the
   archive listing (latest edition + previous ones, direct PDF links).

**The edition PR is the editorial gate (OPS-3).** Its body is the run report: the funnel
(fetched → filtered → scored → selected → written), scores distribution, sources used,
stories re-sourced or dropped (blocked fetches, widened lokaal window), correction
log from S8, typeset-check outcome, and LLM cost. The editor opens the booklet PDF from
the PR, optionally edits `edition.json`/artifacts in place (S9 re-renders), merges to
publish.

## 8. Testing & evaluation

- **Golden run**: recorded feed fixtures + stubbed LLM responses drive S1→S9 to a byte-
  stable edition; catches template and plumbing regressions in CI on every PR.
- **Typeset check** doubles as a test: the golden edition must pass LAY-1..5.

