from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import report, trace
from .context import RunContext
from .fases import f1_fetch, f2_filter, f3_score, f4_select, f5_enrich
from .fases import f6_outline, f7_write, f8_review, f9_compose

FASES: dict[str, object] = {
    "fetch": f1_fetch.run,
    "filter": f2_filter.run,
    "score": f3_score.run,
    "select": f4_select.run,
    "enrich": f5_enrich.run,
    "outline": f6_outline.run,
    "write": f7_write.run,
    "review": f8_review.run,
    "compose": f9_compose.run,
}
FASE_NAMES = list(FASES)


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

    run_p = sub.add_parser("run", help="chain the fases")
    common(run_p)
    run_p.add_argument("--from", dest="from_fase", choices=FASE_NAMES,
                       default=FASE_NAMES[0], help="resume from this fase")
    run_p.add_argument("--until", dest="until_fase", choices=FASE_NAMES,
                       default=FASE_NAMES[-1], help="stop after this fase")

    for name in FASE_NAMES:
        common(sub.add_parser(name, help=f"run fase {name} only"))
    common(sub.add_parser("report", help="regenerate the run report"))
    trace_p = sub.add_parser("trace", help="build viz-trace.json for the replay")
    common(trace_p)
    trace_p.add_argument("--work", type=Path, default=None,
                         help="work dir of a recorded run (default: ctx.work_dir)")
    trace_p.add_argument("--out", type=Path, default=None,
                         help="output path (default: <root>/viz/viz-trace.json)")
    return parser


def run_fase(name: str, ctx: RunContext) -> None:
    FASES[name](ctx)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    ctx = RunContext(root=args.root, edition=args.edition,
                     window_days=args.window_days)

    if args.command == "report":
        report.run(ctx)
        return
    if args.command == "trace":
        trace.run(ctx, work=args.work, out=args.out)
        return
    if args.command != "run":
        run_fase(args.command, ctx)
        report.run(ctx)
        return

    start = FASE_NAMES.index(args.from_fase)
    stop = FASE_NAMES.index(args.until_fase)
    if stop < start:
        raise SystemExit(f"--until '{args.until_fase}' comes before --from '{args.from_fase}'")
    for name in FASE_NAMES[start:stop + 1]:
        run_fase(name, ctx)
    report.run(ctx)
