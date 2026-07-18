# De Zonzijde

A calm, weekly, printable newspaper of genuinely good news for Wijchen and beyond —
built outward in rings: lokaal → regionaal → nationaal → internationaal.

## Documentation

- [`concept_ZZ.md`](concept_ZZ.md) — the original concept/brainstorm document.
- [`docs/SPEC.md`](docs/SPEC.md) — the product & editorial specification: the normative
  rules an edition must satisfy (content mix, layout, typography, fixed elements,
  pipeline behaviour), with stable requirement IDs and open questions.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the system design for the automation
  pipeline: stages S1–S9, data contracts, orchestration via GitHub Actions with a human
  editorial gate, target repo layout, and the build order.

## Current assets

| File | What it is |
|------|-----------|
| `proto_krant.html` | Hand-built edition prototype — the target look & feel (19 juli 2026). |
| `proto_fetchfilter.html` | Browser app: fetch RSS sources, regex filters, LLM scoring, export candidate table. |
| `proto_index.html` | Earlier in-browser edition generator (superseded, kept for reference). |
| `tools/fetch-articles.py` | Fetches full article text behind selected links (with headless-browser fallback). |
| `tools/build-fonts.py` | Builds the self-hosted font subsets in `fonts/`. |
| `fonts/`, `fonts.css` | Self-hosted Fraunces / Newsreader / Archivo for offline-correct print. |
| `.github/workflows/pages.yml` | Deploys the repo to GitHub Pages. |
