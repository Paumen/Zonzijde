"""Scorer eval (ARCHITECTURE §9): run prompts/score.md over the labelled set.

Two tracked numbers:

- **negativity leakage** — items labelled ≤0 that score ≥+1. The trust-killer:
  a leaked negative story ends up in a good-news paper. Keep ~0.
- **positive recall** — items labelled ≥+1 that score ≥+1.

Any change to ``prompts/score.md``, the light model, or the filter buckets
must re-run this eval and post the numbers in its PR.

This is a live-API script, not a pytest test (hence no ``test_`` prefix):

    GEMINI_API_KEY=... python3 tests/eval_score.py [--labels PATH] [--root DIR]

It reuses the S3 batching/parsing path verbatim, so the eval measures exactly
what the stage does — including fail-closed exclusion (unscored counts as a
recall miss, never as leakage).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from zonzijde import llm, prompts  # noqa: E402
from zonzijde.context import TZ, RunContext  # noqa: E402
from zonzijde.contracts import FeedItem  # noqa: E402
from zonzijde.stages import score  # noqa: E402


def load_labels(path: Path) -> list[dict]:
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def as_item(row: dict) -> FeedItem:
    return FeedItem(
        id=row["id"], source="eval", bron=row["bron"], scopes=["N"],
        title=row["titel"], link=f"https://eval.invalid/{row['id']}",
        summary=row["samenvatting"], published=None,
        fetched=datetime(2026, 1, 1, tzinfo=TZ))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", type=Path,
                        default=REPO_ROOT / "tests" / "eval" / "score-labels.jsonl")
    parser.add_argument("--root", type=Path, default=REPO_ROOT,
                        help="repo root with config/ (prompt + model under eval)")
    args = parser.parse_args()

    ctx = RunContext(root=args.root, edition=datetime.now(TZ).date())
    cfg = ctx.llm_cfg("light")
    prompt = prompts.load_prompt(args.root, "score")
    call = lambda p: llm.light_json(p, model=cfg["model"])

    rows = load_labels(args.labels)
    items = [as_item(r) for r in rows]
    batch_size = int(cfg.get("batch_size", 80))
    batches = [items[off:off + batch_size]
               for off in range(0, len(items), batch_size)]

    scores: dict[str, int] = {}
    for n, batch in enumerate(batches, 1):
        got, problems = score.score_batch(prompt.body, batch, call)
        for k, item in enumerate(batch):
            if k + 1 in got:
                scores[item.id] = got[k + 1]
        print(f"batch {n}/{len(batches)}: {len(got)}/{len(batch)} scored"
              + (f" — problems: {problems}" if problems else ""))

    labelled_neg = [r for r in rows if r["label"] <= 0]
    labelled_pos = [r for r in rows if r["label"] >= 1]
    leaked = [r for r in labelled_neg if scores.get(r["id"], -99) >= 1]
    recalled = [r for r in labelled_pos if scores.get(r["id"], -99) >= 1]
    unscored = [r for r in rows if r["id"] not in scores]

    confusion = Counter((r["label"], scores.get(r["id"], "·")) for r in rows)
    print(f"\n## Scorer eval — score.md v{prompt.version}, model {cfg['model']},"
          f" {len(rows)} labelled items")
    print(f"\n- negativity leakage: {len(leaked)}/{len(labelled_neg)}"
          f" ({len(leaked) / len(labelled_neg):.1%}) — keep ~0")
    print(f"- positive recall:    {len(recalled)}/{len(labelled_pos)}"
          f" ({len(recalled) / len(labelled_pos):.1%})")
    print(f"- unscored (fail-closed): {len(unscored)}")

    print("\n| label \\ score | -2 | -1 | 0 | +1 | +2 | unscored |")
    print("|---|---|---|---|---|---|---|")
    for label in (-2, -1, 0, 1, 2):
        cells = [confusion.get((label, s), 0) for s in (-2, -1, 0, 1, 2, "·")]
        print(f"| {label:+d} | " + " | ".join(str(c) for c in cells) + " |")

    if leaked:
        print("\nLeaked items (labelled ≤0, scored ≥+1):")
        for r in leaked:
            print(f"- [{r['label']:+d} → +{scores[r['id']]}] {r['bron']}: {r['titel']}")


if __name__ == "__main__":
    main()
