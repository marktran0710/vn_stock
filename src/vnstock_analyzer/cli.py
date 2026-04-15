from __future__ import annotations

import argparse
from pathlib import Path

from .config import DEFAULT_PERIODS, TOP200_DEFAULT_PATH
from .services import build_compare_analysis, build_universe_scan_analysis
from .reporting import (
    analysis_result_to_payload,
    render_report,
    render_universe_scan,
    to_json_file,
    universe_result_to_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze VN stock performance across multiple timeframes and compare symbols."
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        help="VN stock tickers with Yahoo suffix like VCB.VN FPT.VN MWG.VN",
    )
    parser.add_argument(
        "--benchmark",
        default=None,
        help="Optional benchmark ticker for relative strength comparison",
    )
    parser.add_argument(
        "--periods",
        nargs="*",
        default=DEFAULT_PERIODS,
        help="Analysis periods such as 1mo 2mo 3mo 6mo 1y 2y 3y",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write report as JSON to this path",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Save a normalized comparison chart",
    )
    parser.add_argument(
        "--plot-file",
        type=Path,
        default=Path("vn_stock_comparison.png"),
        help="Chart output file path when --plot is enabled",
    )
    parser.add_argument(
        "--market-scan",
        action="store_true",
        help="Analyze the top VN universe file and summarize market fluctuation",
    )
    parser.add_argument(
        "--universe-file",
        type=Path,
        default=TOP200_DEFAULT_PATH,
        help="CSV file containing VN stock universe with a 'symbol' column",
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=200,
        help="Number of symbols to scan from the universe file",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top join candidates to return in market-scan mode",
    )
    return parser.parse_args()


def run_compare_mode(args: argparse.Namespace) -> int:
    try:
        result, failures = build_compare_analysis(args.symbols, args.periods, benchmark=args.benchmark)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(render_report(result))

    if args.output:
        to_json_file(args.output, analysis_result_to_payload(result))
        print(f"\nSaved JSON report to {args.output}")

    if failures:
        print(f"\nSkipped optional symbols due to missing data: {', '.join(failures)}")
    return 0


def run_market_scan_mode(args: argparse.Namespace) -> int:
    try:
        result, failures = build_universe_scan_analysis(
            universe_file=args.universe_file,
            periods=args.periods,
            benchmark=args.benchmark,
            scan_limit=args.scan_limit,
            top_n=args.top_n,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(render_universe_scan(result))

    if args.output:
        to_json_file(args.output, universe_result_to_payload(result))
        print(f"\nSaved JSON report to {args.output}")

    return 0


def main() -> int:
    args = parse_args()
    if args.market_scan:
        return run_market_scan_mode(args)
    return run_compare_mode(args)
