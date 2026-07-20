from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import report
from .context import RunContext
from .stages import (compose, enrich, fetch, filter as filter_stage, outline,
                     review, score, select, write)

STAGES: dict[str, object] = {
    "fetch": fetch.run,
    "filter": filter_stage.run,
    "score": score.run,
    "select": select.run,
    "enrich": enrich.run,
    "outline": outline.run,
    "write": write.run,
    "review": review.run,
    "compose": compose.run,
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
    STAGES[name](ctx)


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
