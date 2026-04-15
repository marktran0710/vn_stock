from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .analytics import (
    analyze_sector_groups,
    build_metrics,
    describe_market_fluctuation,
    recommend_top_join_stocks,
    summarize_comparison,
)
from .config import DEFAULT_PERIODS, TOP200_DEFAULT_PATH
from .data import load_history, load_universe_dataframe
from .models import AnalysisResult, UniverseScanResult


def build_compare_analysis(symbols: list[str], periods: list[str], benchmark: str | None = None) -> tuple[AnalysisResult, list[str]]:
    normalized_symbols = list(dict.fromkeys([item.upper() for item in symbols]))
    if len(normalized_symbols) < 2:
        raise ValueError("Provide 2 or 3 symbols for comparison.")
    if len(normalized_symbols) > 3:
        raise ValueError("Please provide at most 3 symbols in compare mode.")

    normalized_periods = list(dict.fromkeys(periods))
    benchmark_symbol = benchmark.upper() if benchmark else None
    requested = normalized_symbols + ([benchmark_symbol] if benchmark_symbol and benchmark_symbol not in normalized_symbols else [])

    history: dict[str, pd.DataFrame] = {}
    failures: list[str] = []
    for symbol in requested:
        try:
            history[symbol] = load_history(symbol, normalized_periods)
        except Exception:
            failures.append(symbol)

    missing_required = [symbol for symbol in normalized_symbols if symbol in failures]
    if missing_required:
        raise ValueError(f"Failed to load required symbol(s): {', '.join(missing_required)}")

    benchmark_series = history.get(benchmark_symbol)["Close"] if benchmark_symbol and benchmark_symbol in history else None
    metrics = [
        build_metrics(symbol, history[symbol], benchmark_series if symbol != benchmark_symbol else None, normalized_periods)
        for symbol in normalized_symbols
    ]

    result = AnalysisResult(
        as_of=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        benchmark=benchmark_symbol,
        symbols=normalized_symbols,
        metrics=metrics,
        market_fluctuation_summary=describe_market_fluctuation(benchmark_series),
        comparison_summary=summarize_comparison(metrics, normalized_periods),
        notes=[
            "Uses end-of-day market data and a quantitative framework.",
            "Data coverage for some VN tickers can be incomplete; verify ticker suffixes if data is missing.",
            "Educational analysis only, not financial advice.",
        ],
    )
    return result, failures


def build_universe_scan_analysis(
    universe_file: Path = TOP200_DEFAULT_PATH,
    periods: list[str] | None = None,
    benchmark: str | None = None,
    scan_limit: int = 200,
    top_n: int = 10,
) -> tuple[UniverseScanResult, list[str]]:
    normalized_periods = list(dict.fromkeys(periods or DEFAULT_PERIODS))
    if "3mo" not in normalized_periods:
        normalized_periods.append("3mo")

    universe_df = load_universe_dataframe(universe_file, limit=scan_limit)
    universe_symbols = universe_df["symbol"].tolist()
    sector_by_symbol = {
        row["symbol"]: row["notes"]
        for _, row in universe_df.iterrows()
    }
    benchmark_symbol = benchmark.upper() if benchmark else None
    requested = universe_symbols + ([benchmark_symbol] if benchmark_symbol and benchmark_symbol not in universe_symbols else [])

    history: dict[str, pd.DataFrame] = {}
    failures: list[str] = []
    for symbol in requested:
        try:
            history[symbol] = load_history(symbol, normalized_periods)
        except Exception:
            failures.append(symbol)

    benchmark_series = history.get(benchmark_symbol)["Close"] if benchmark_symbol and benchmark_symbol in history else None

    metrics = []
    for symbol in universe_symbols:
        if symbol in history:
            metrics.append(build_metrics(symbol, history[symbol], benchmark_series if symbol != benchmark_symbol else None, normalized_periods))

    if not metrics:
        raise ValueError("No symbols were analyzable from the selected universe file.")

    average_returns: dict[str, float] = {}
    for period in normalized_periods:
        values = [item.returns.get(period) for item in metrics if item.returns.get(period) is not None]
        if values:
            average_returns[period] = round(sum(values) / len(values), 2)

    scored_3m = [(item.symbol, item.returns.get("3mo")) for item in metrics if item.returns.get("3mo") is not None]
    scored_3m.sort(key=lambda row: row[1], reverse=True)
    top_gainers = [(symbol, value) for symbol, value in scored_3m[:10]]
    top_losers = [(symbol, value) for symbol, value in scored_3m[-10:]]
    top_join_candidates = recommend_top_join_stocks(metrics, top_n=top_n)
    sector_group_analysis = analyze_sector_groups(metrics, sector_by_symbol, periods=["3mo", "6mo", "1y"], top_n=3)

    result = UniverseScanResult(
        as_of=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        benchmark=benchmark_symbol,
        total_symbols=len(universe_symbols),
        analyzed_symbols=len(metrics),
        average_returns=average_returns,
        top_gainers_3m=top_gainers,
        top_losers_3m=top_losers,
        top_join_candidates_now=top_join_candidates,
        sector_group_analysis=sector_group_analysis,
        market_fluctuation_summary=describe_market_fluctuation(benchmark_series),
        notes=[
            "Universe scan is sensitive to missing symbols or limited Yahoo Finance coverage.",
            f"Failed downloads: {len(failures)} symbol(s).",
            "Educational analysis only, not financial advice.",
        ],
    )
    return result, failures
