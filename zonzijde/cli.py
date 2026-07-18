"""CLI: ``python -m zonzijde <stage>|run|report --edition YYYY-MM-DD``.

``run`` chains the stages; ``--from``/``--until`` re-run a slice against
existing artifacts (ARCHITECTURE §3). Stages beyond the current build phase
(§11) exist in the registry but are not implemented yet — hitting one stops
the run with a clear message instead of guessing.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import report
from .context import RunContext
from .stages import fetch, filter as filter_stage, score, select

# S1–S9 in funnel order; None marks stages of a later build phase (§11).
STAGES: dict[str, object] = {
    "fetch": fetch.run,         # S1  phase 1
    "filter": filter_stage.run,  # S2  phase 1
    "score": score.run,         # S3  phase 2
    "select": select.run,       # S4  phase 2
    "enrich": None,             # S5  phase 3
    "outline": None,            # S6  phase 4
    "write": None,              # S7  phase 4
    "review": None,             # S8  phase 4
    "compose": None,            # S9  phase 5
}
STAGE_NAMES = list(STAGES)


def parse_edition(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m zonzijde",
        description="De Zonzijde pipeline (docs/ARCHITECTURE.md)")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--edition", type=parse_edition, required=True,
                       metavar="YYYY-MM-DD", help="edition date (a Sunday, OPS-1)")
        p.add_argument("--window-days", type=int, default=None,
                       help="override the candidate window (SRC-4)")
        p.add_argument("--root", type=Path, default=Path.cwd(),
                       help="repo root (default: current directory)")

    run_p = sub.add_parser("run", help="chain the stages")
    common(run_p)
    run_p.add_argument("--from", dest="from_stage", choices=STAGE_NAMES,
                       default=STAGE_NAMES[0], help="resume from this stage")
    run_p.add_argument("--until", dest="until_stage", choices=STAGE_NAMES,
                       default=STAGE_NAMES[-1], help="stop after this stage")

    for name in STAGE_NAMES:
        common(sub.add_parser(name, help=f"run stage {name} only"))
    common(sub.add_parser("report", help="regenerate the run report"))
    return parser


def run_stage(name: str, ctx: RunContext) -> None:
    fn = STAGES[name]
    if fn is None:
        phase = {"enrich": 3, "outline": 4, "write": 4,
                 "review": 4, "compose": 5}[name]
        raise SystemExit(
            f"stage '{name}' is not implemented yet — build phase {phase} "
            f"(docs/ARCHITECTURE.md §11)")
    fn(ctx)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    ctx = RunContext(root=args.root, edition=args.edition,
                     window_days=args.window_days)

    if args.command == "report":
        report.run(ctx)
        return
    if args.command != "run":
        run_stage(args.command, ctx)
        report.run(ctx)
        return

    start = STAGE_NAMES.index(args.from_stage)
    stop = STAGE_NAMES.index(args.until_stage)
    if stop < start:
        raise SystemExit(f"--until '{args.until_stage}' comes before --from '{args.from_stage}'")
    for name in STAGE_NAMES[start:stop + 1]:
        run_stage(name, ctx)
    report.run(ctx)
