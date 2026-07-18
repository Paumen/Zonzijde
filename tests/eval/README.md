# Scorer eval labelled set

`score-labels.jsonl` — one item per line: `id`, `bron`, `titel`,
`samenvatting`, `label` (−2…+2 per the rubric in `config/prompts/score.md`).

**Provenance (v1):** all 215 items are *real* feed items from the S1+S2 run of
2026-07-18 (edition window 2026-07-19) — the exact stream the scorer sees
after the bucket filter. The labels were assigned by Claude while building
the pipeline (phase 2), **not yet reviewed by the editor**. ARCHITECTURE §9
calls for a hand-labelled set: treat these labels as a seed to correct, not
as ground truth. Editing a `label` value is enough; the harness picks it up.

Run the eval (live light-tier calls, ~3 batches; auth via ANTHROPIC_API_KEY
or ambient Claude Code credentials):

```bash
python3 tests/eval_score.py
```

Two tracked numbers (§9): **negativity leakage** (labelled ≤0 scoring ≥+1 —
keep ~0) and **positive recall**. Any change to `prompts/score.md`, the light
model, or the buckets must re-run this eval and post the numbers in its PR.
