from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd

from .config import DEFAULT_PERIODS, TOP200_DEFAULT_PATH
from .services import build_compare_analysis, build_universe_scan_analysis
from .services import get_stock_details, get_sector_peers
from .analytics import (
    get_stock_historical_data,
    get_financial_ratios,
    get_realtime_price,
    calculate_technical_indicators,
)
from .reporting import (
    analysis_result_to_payload,
    render_buy_potential,
    render_report,
    render_universe_scan,
    to_json_file,
    universe_result_to_payload,
)


def _json_safe(value):
    """Convert nested objects into JSON-serializable structures with string keys."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_dict"):
        try:
            return _json_safe(value.to_dict())
        except Exception:
            return str(value)
    return value


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
        "--buy-potential",
        action="store_true",
        help="Analyze the universe and return buy-potential candidates",
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
    parser.add_argument(
        "--min-buy-score",
        type=float,
        default=0.0,
        help="Minimum score threshold in buy-potential mode",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Fetch and display stock details (financials, technical indicators, real-time price)",
    )
    parser.add_argument(
        "--technicals",
        action="store_true",
        help="Calculate and display technical indicators (SMA, RSI)",
    )
    parser.add_argument(
        "--financials",
        action="store_true",
        help="Fetch and display financial ratios (P/E, ROE, ROA, etc.)",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Fetch and display real-time stock price and market data",
    )
    parser.add_argument(
        "--peers",
        action="store_true",
        help="Compare stock with sector peers",
    )
    parser.add_argument(
        "--metric",
        type=str,
        default="P/E",
        help="Financial metric to compare with peers (e.g., P/E, ROE, ROA, Debt/Equity)",
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


def run_buy_potential_mode(args: argparse.Namespace) -> int:
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

    print(render_buy_potential(result, min_score=args.min_buy_score))

    if args.output:
        payload = universe_result_to_payload(result)
        payload["min_buy_score"] = args.min_buy_score
        payload["buy_potential_filtered"] = [
            row for row in result.buy_potential_candidates if row[1] >= args.min_buy_score
        ]
        to_json_file(args.output, payload)
        print(f"\nSaved JSON report to {args.output}")

    if failures:
        print(f"\nSkipped symbols with missing data: {len(failures)}")
    return 0


def run_stock_details_mode(args: argparse.Namespace) -> int:
    """Fetch comprehensive stock details."""
    if not args.symbols or len(args.symbols) < 1:
        raise SystemExit("Please provide a stock symbol (e.g., VCB.VN)")
    
    symbol = args.symbols[0]
    details = get_stock_details(symbol)
    
    print(f"\n{'='*60}")
    print(f"STOCK DETAILS: {symbol}")
    print(f"{'='*60}\n")
    
    if details.get("realtime_price"):
        print("REAL-TIME PRICE:")
        realtime_payload = _json_safe(details["realtime_price"])
        print(json.dumps(realtime_payload, indent=2, ensure_ascii=False, default=str))
        print()
    
    if details.get("financial_ratios"):
        print("FINANCIAL RATIOS:")
        print(json.dumps(_json_safe(details["financial_ratios"]), indent=2, ensure_ascii=False, default=str))
        print()
    
    if details.get("technical_indicators"):
        print("TECHNICAL INDICATORS (Latest values):")
        for name, series in details["technical_indicators"].items():
            if hasattr(series, 'iloc') and not series.empty:
                latest = series.iloc[-1]
                print(f"  {name}: {latest:.2f}")
        print()
    else:
        print("TECHNICAL INDICATORS: unavailable")
        print()
    
    if args.output:
        output_data = {
            "symbol": symbol,
            "realtime_price": _json_safe(details.get("realtime_price")),
            "financial_ratios": _json_safe(details.get("financial_ratios")),
            "technical_indicators": {
                k: float(v.iloc[-1]) if hasattr(v, 'iloc') and not v.empty else None
                for k, v in (details.get("technical_indicators") or {}).items()
            }
        }
        to_json_file(args.output, output_data)
        print(f"Saved details to {args.output}")
    
    return 0


def run_technicals_mode(args: argparse.Namespace) -> int:
    """Calculate and display technical indicators."""
    if not args.symbols or len(args.symbols) < 1:
        raise SystemExit("Please provide a stock symbol (e.g., VCB.VN)")
    
    symbol = args.symbols[0]
    print(f"\n{'='*60}")
    print(f"TECHNICAL ANALYSIS: {symbol}")
    print(f"{'='*60}\n")
    
    historical_data = get_stock_historical_data(symbol)
    if historical_data is None or historical_data.empty:
        print(f"Could not fetch historical data for {symbol}")
        return 1
    
    indicators = calculate_technical_indicators(historical_data, sma_periods=[20, 50, 200])
    
    if indicators:
        print("TECHNICAL INDICATORS (Latest values):")
        for name, series in indicators.items():
            if hasattr(series, 'iloc') and not series.empty:
                latest = series.iloc[-1]
                if pd.notna(latest):
                    print(f"  {name}: {latest:.2f}")
        print()
    else:
        print("No technical indicators could be calculated.")
        return 1
    
    if args.output:
        output_data = {
            "symbol": symbol,
            "technical_indicators": {
                k: float(v.iloc[-1]) if hasattr(v, 'iloc') and not v.empty else None
                for k, v in (indicators or {}).items()
            }
        }
        to_json_file(args.output, output_data)
        print(f"Saved technical analysis to {args.output}")
    
    return 0


def run_financials_mode(args: argparse.Namespace) -> int:
    """Fetch and display financial ratios."""
    if not args.symbols or len(args.symbols) < 1:
        raise SystemExit("Please provide a stock symbol (e.g., VCB.VN)")
    
    symbol = args.symbols[0]
    print(f"\n{'='*60}")
    print(f"FINANCIAL RATIOS: {symbol}")
    print(f"{'='*60}\n")
    
    ratios = get_financial_ratios(symbol)
    
    if ratios:
        print(json.dumps(_json_safe(ratios), indent=2, ensure_ascii=False, default=str))
        print()
    else:
        print(f"Could not fetch financial ratios for {symbol}")
        return 1
    
    if args.output:
        to_json_file(args.output, {"symbol": symbol, "financial_ratios": _json_safe(ratios)})
        print(f"Saved financial ratios to {args.output}")
    
    return 0


def run_realtime_mode(args: argparse.Namespace) -> int:
    """Fetch and display real-time stock price."""
    if not args.symbols or len(args.symbols) < 1:
        raise SystemExit("Please provide a stock symbol (e.g., VCB.VN)")
    
    symbol = args.symbols[0]
    print(f"\n{'='*60}")
    print(f"REAL-TIME PRICE: {symbol}")
    print(f"{'='*60}\n")
    
    price_data = get_realtime_price(symbol)
    
    if price_data:
        print(json.dumps(_json_safe(price_data), indent=2, ensure_ascii=False, default=str))
        print()
    else:
        print(f"Could not fetch real-time price for {symbol}")
        return 1
    
    if args.output:
        to_json_file(args.output, {"symbol": symbol, "realtime_price": _json_safe(price_data)})
        print(f"Saved real-time price to {args.output}")
    
    return 0


def run_peers_mode(args: argparse.Namespace) -> int:
    """Compare stock with sector peers."""
    if not args.symbols or len(args.symbols) < 1:
        raise SystemExit("Please provide a stock symbol (e.g., VCB.VN)")
    
    symbol = args.symbols[0]
    print(f"\n{'='*60}")
    print(f"PEER COMPARISON: {symbol}")
    print(f"Metric: {args.metric}")
    print(f"{'='*60}\n")
    
    comparison = get_sector_peers(symbol, metric=args.metric)
    
    if comparison.get("peer_comparison"):
        print("PEER COMPARISON DATA:")
        print(json.dumps(_json_safe(comparison["peer_comparison"]), indent=2, ensure_ascii=False, default=str))
        print()
    else:
        print(f"Could not fetch peer comparison data for {symbol}")
    
    if comparison.get("own_ratios"):
        print(f"\n{symbol} FINANCIAL RATIOS:")
        print(json.dumps(_json_safe(comparison["own_ratios"]), indent=2, ensure_ascii=False, default=str))
        print()
    
    if args.output:
        to_json_file(args.output, _json_safe(comparison))
        print(f"Saved peer comparison to {args.output}")
    
    return 0


def main() -> int:
    args = parse_args()
    
    if args.details:
        return run_stock_details_mode(args)
    elif args.technicals:
        return run_technicals_mode(args)
    elif args.financials:
        return run_financials_mode(args)
    elif args.realtime:
        return run_realtime_mode(args)
    elif args.peers:
        return run_peers_mode(args)
    elif args.buy_potential:
        return run_buy_potential_mode(args)
    elif args.market_scan:
        return run_market_scan_mode(args)
    else:
        return run_compare_mode(args)
