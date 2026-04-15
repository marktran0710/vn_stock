from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from .data import align_series
from .models import AnalysisResult, UniverseScanResult


def render_report(result: AnalysisResult) -> str:
    lines = []
    lines.append(f"VN Stock Fluctuation Analysis as of {result.as_of}")
    lines.append(f"Symbols: {', '.join(result.symbols)}")
    if result.benchmark:
        lines.append(f"Benchmark: {result.benchmark}")
    lines.append("")
    lines.append(f"Market fluctuation: {result.market_fluctuation_summary}")
    lines.append(f"Comparison: {result.comparison_summary}")
    lines.append("")

    for metric in result.metrics:
        lines.append(f"{metric.symbol}")
        lines.append(f"  Latest close: {metric.latest_close:.2f}" if metric.latest_close is not None else "  Latest close: n/a")
        lines.append(
            f"  Volatility (30d annualized): {metric.volatility_30d:.2f}%" if metric.volatility_30d is not None else "  Volatility (30d annualized): n/a"
        )
        lines.append(
            f"  Max drawdown (1Y): {metric.max_drawdown_1y:.2f}%" if metric.max_drawdown_1y is not None else "  Max drawdown (1Y): n/a"
        )
        lines.append(
            f"  Trend score: {metric.trend_score:.2f}" if metric.trend_score is not None else "  Trend score: n/a"
        )
        if metric.relative_strength_1y is not None:
            lines.append(f"  Relative strength vs benchmark (1Y): {metric.relative_strength_1y:.2f}%")
        lines.append("  Returns:")
        for period, value in metric.returns.items():
            if value is None:
                lines.append(f"    {period}: n/a")
            else:
                lines.append(f"    {period}: {value:.2f}%")
        lines.append("")

    lines.append("Notes:")
    for note in result.notes:
        lines.append(f"- {note}")
    return "\n".join(lines)


def render_universe_scan(result: UniverseScanResult) -> str:
    lines = []
    lines.append(f"VN Top Universe Market Scan as of {result.as_of}")
    lines.append(f"Universe size: {result.total_symbols}, analyzed: {result.analyzed_symbols}")
    if result.benchmark:
        lines.append(f"Benchmark: {result.benchmark}")
    lines.append("")
    lines.append(f"Market fluctuation: {result.market_fluctuation_summary}")
    lines.append("")
    lines.append("Average returns by period:")
    for period, value in result.average_returns.items():
        lines.append(f"- {period}: {value:.2f}%")
    lines.append("")
    lines.append("Top gainers (3M):")
    for symbol, value in result.top_gainers_3m:
        lines.append(f"- {symbol}: {value:.2f}%")
    lines.append("")
    lines.append("Top losers (3M):")
    for symbol, value in result.top_losers_3m:
        lines.append(f"- {symbol}: {value:.2f}%")
    lines.append("")
    lines.append("Top join candidates now:")
    for symbol, score, rationale in result.top_join_candidates_now:
        lines.append(f"- {symbol}: score {score:.4f} ({rationale})")
    lines.append("")
    lines.append("Sector group analysis (3M / 6M / 12M):")
    for period in ["3mo", "6mo", "1y"]:
        if period not in result.sector_group_analysis:
            continue
        lines.append(f"- {period}")
        groups = result.sector_group_analysis[period]
        for group_name in ["pillar", "growth", "sustainable"]:
            rows = groups.get(group_name, [])
            if not rows:
                continue
            preview = ", ".join([f"{sector} ({score:.2f}, n={count})" for sector, score, count in rows])
            lines.append(f"  {group_name}: {preview}")
    lines.append("")
    lines.append("Notes:")
    for note in result.notes:
        lines.append(f"- {note}")
    return "\n".join(lines)


def to_json_file(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def analysis_result_to_payload(result: AnalysisResult) -> dict:
    return {
        "as_of": result.as_of,
        "benchmark": result.benchmark,
        "symbols": result.symbols,
        "metrics": [dataclasses.asdict(metric) for metric in result.metrics],
        "market_fluctuation_summary": result.market_fluctuation_summary,
        "comparison_summary": result.comparison_summary,
        "notes": result.notes,
    }


def universe_result_to_payload(result: UniverseScanResult) -> dict:
    return {
        "as_of": result.as_of,
        "benchmark": result.benchmark,
        "total_symbols": result.total_symbols,
        "analyzed_symbols": result.analyzed_symbols,
        "average_returns": result.average_returns,
        "top_gainers_3m": result.top_gainers_3m,
        "top_losers_3m": result.top_losers_3m,
        "top_join_candidates_now": result.top_join_candidates_now,
        "sector_group_analysis": getattr(result, "sector_group_analysis", {}),
        "market_fluctuation_summary": result.market_fluctuation_summary,
        "notes": result.notes,
    }


def plot_comparison(history: dict[str, pd.DataFrame], output_file: Path) -> Path | None:
    if plt is None:
        return None

    combined = align_series(history)
    if combined.empty:
        return None

    normalized = combined / combined.iloc[0] * 100.0
    ax = normalized.plot(figsize=(12, 7), linewidth=2)
    ax.set_title("VN Stock Relative Performance")
    ax.set_ylabel("Normalized price (base 100)")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    return output_file
