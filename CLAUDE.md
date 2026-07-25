## What this is

De Zonzijde is a weekly, printable Dutch newspaper of genuinely good news for
Gemeente Wijchen and outward (lokaal → regionaal → nationaal → internationaal).
The deliverable is a print-ready PDF (A3 booklet imposition). For more see `brief.md`.

**The two documents that govern all work here:**

- `docs/SPEC.md` — the *what*: editorial and layout rules an edition must satisfy.
  
- `docs/ARCHITECTURE.md` — the *how*: the pipeline design, data contracts,
  target repo layout (`zonzijde/` Python package), Typst typesetting, orchestration,
  and the phased build order.

- `config/prompts/brief.md` - explains the *why* vision, concept, concept of the paper.

The original concept is archived at `docs/history/concept_ZZ.md`.

## Running the pipeline

Requires Python ≥3.11 and the `claude` CLI on `PATH` (the frontier fases go through
the Agent SDK). Install once, editable, with the headless-browser extra F5 uses:

```
python3 -m venv .venv
.venv/bin/pip install -e ".[browser]"
```

Always invoke from the repo root — `RunContext` resolves `config/` and `editions/`
relative to `--root`, which defaults to the current directory.

```
.venv/bin/python -m zonzijde run     --edition 2026-07-26                    # F1–F9
.venv/bin/python -m zonzijde run     --edition 2026-07-26 --from score --until write
.venv/bin/python -m zonzijde score   --edition 2026-07-26                    # one fase
.venv/bin/python -m zonzijde report  --edition 2026-07-26                    # report only
```

Fase names, in order: `fetch filter score select enrich outline write review compose`.
`--window-days` overrides `window.days`; `--root` points at another checkout.

Artifacts land in `editions/<edition>/` (gitignored): `work/` holds each fase's output
and its `*-log.json`, alongside `report.md`, `edition.json` and the composed PDF. A
finished run is snapshotted by copying that directory under `reports/`.

Every fase reads the fase before it from `work/`, so a resumed range needs the earlier
artifacts already present. See `docs/ARCHITECTURE.md` for the fase contracts, and the
approval rules below before invoking any of this.

## Conventions and hard rules

- Specification, decision, instructions, etc. live in one place, remainder refers to it.
- Do NOT add comments and docstrings to code files. Except if absolutely necessary to prevent a frontier LLM agent making specific errors when editing the code in future.
- Never refer to or repeat specs or rules or decisions in code files.
- - Never create or edit tests without explicit PO approval. You must explain PO proposed test and why you think it's critical in plain English inline in chat before you can request approval.
- Never edit prompt files without explicit approval PO. You must show PO exact current and proposed prompt instruction inline in chat before you can request approval. This includes what goes into system prompt, json schema and description, anything else injected to llm api or sdk agent.
- When a fase fails, diagnose by replaying one failing item (its log holds `system` and every `prompt`) and reading the raw message stream — never by re-running the fase. Do not retry, raise a limit, or change anything until you can name the mechanism.
- Never run or re-run a fase, a range of fases, or the whole pipeline without explicit PO approval — every run costs money and time. Ask first, every time, including after a change you believe fixes the failure.

