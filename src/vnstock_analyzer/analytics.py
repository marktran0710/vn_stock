from __future__ import annotations

import math

import pandas as pd

from .config import PERIOD_TO_DAYS
from .models import StockMetrics


def compute_return(series: pd.Series, lookback_days: int) -> float | None:
    if series.empty or len(series) < 2:
        return None
    end_price = float(series.iloc[-1])
    target_date = series.index[-1] - pd.Timedelta(days=lookback_days)
    historical = series.loc[:target_date]
    if historical.empty:
        return None
    start_price = float(historical.iloc[-1])
    if start_price == 0:
        return None
    return (end_price / start_price - 1.0) * 100.0


def compute_max_drawdown(series: pd.Series) -> float | None:
    if series.empty:
        return None
    running_max = series.cummax()
    drawdowns = series / running_max - 1.0
    return float(drawdowns.min() * 100.0)


def compute_trend_score(series: pd.Series) -> float | None:
    if series.empty or len(series) < 40:
        return None
    recent = series.tail(120)
    short_ma = recent.rolling(20).mean().iloc[-1]
    long_ma = recent.rolling(60).mean().iloc[-1]
    if pd.isna(short_ma) or pd.isna(long_ma) or long_ma == 0:
        return None
    momentum = (recent.iloc[-1] / recent.iloc[0] - 1.0) * 100.0
    ma_spread = (short_ma / long_ma - 1.0) * 100.0
    return round(momentum * 0.6 + ma_spread * 0.4, 2)


def compute_annualized_volatility(series: pd.Series, window: int = 30) -> float | None:
    if len(series) < window + 1:
        return None
    returns = series.pct_change().dropna().tail(window)
    if returns.empty:
        return None
    return float(returns.std() * math.sqrt(252) * 100.0)


def compute_relative_strength(stock_series: pd.Series, benchmark_series: pd.Series, lookback_days: int) -> float | None:
    aligned = pd.concat([stock_series, benchmark_series], axis=1, keys=["stock", "benchmark"]).dropna()
    if aligned.empty:
        return None
    cutoff = aligned.index[-1] - pd.Timedelta(days=lookback_days)
    aligned = aligned.loc[aligned.index >= cutoff]
    if len(aligned) < 2:
        return None
    stock_return = aligned["stock"].iloc[-1] / aligned["stock"].iloc[0] - 1.0
    benchmark_return = aligned["benchmark"].iloc[-1] / aligned["benchmark"].iloc[0] - 1.0
    return round((stock_return - benchmark_return) * 100.0, 2)


def describe_market_fluctuation(benchmark_series: pd.Series | None) -> str:
    if benchmark_series is None or benchmark_series.empty:
        return "Benchmark unavailable, so market regime is inferred from cross-stock relative moves only."

    latest = float(benchmark_series.iloc[-1])
    ma20 = benchmark_series.rolling(20).mean().iloc[-1]
    ma60 = benchmark_series.rolling(60).mean().iloc[-1]
    vol30 = compute_annualized_volatility(benchmark_series, 30)
    drawdown = compute_max_drawdown(benchmark_series.tail(252))

    if pd.isna(ma20) or pd.isna(ma60):
        regime = "insufficient data"
    elif latest >= ma20 >= ma60:
        regime = "risk-on / upward regime"
    elif latest <= ma20 <= ma60:
        regime = "risk-off / downward regime"
    else:
        regime = "mixed or transition regime"

    vol_text = f"30d annualized volatility around {vol30:.1f}%" if vol30 is not None else "volatility unavailable"
    dd_text = f"1Y max drawdown near {drawdown:.1f}%" if drawdown is not None else "drawdown unavailable"
    return f"Benchmark signals a {regime}; {vol_text}; {dd_text}."


def build_metrics(symbol: str, data: pd.DataFrame, benchmark: pd.Series | None, periods: list[str]) -> StockMetrics:
    close = data["Close"]
    returns = {period: compute_return(close, PERIOD_TO_DAYS.get(period, 365)) for period in periods}
    benchmark_rs = None
    if benchmark is not None:
        benchmark_rs = compute_relative_strength(close, benchmark, 365)

    latest = float(close.iloc[-1]) if not close.empty else None
    return StockMetrics(
        symbol=symbol,
        latest_close=latest,
        returns=returns,
        volatility_30d=compute_annualized_volatility(close, 30),
        max_drawdown_1y=compute_max_drawdown(close.tail(252)),
        trend_score=compute_trend_score(close),
        relative_strength_1y=benchmark_rs,
    )


def summarize_comparison(metrics: list[StockMetrics], periods: list[str]) -> str:
    if len(metrics) < 2:
        return "Need at least 2 symbols for a meaningful comparison."

    rows = []
    for metric in metrics:
        best_period = None
        best_return = None
        for period in periods:
            value = metric.returns.get(period)
            if value is None:
                continue
            if best_return is None or value > best_return:
                best_period = period
                best_return = value
        trend_value = metric.trend_score if metric.trend_score is not None else float("-inf")
        return_value = best_return if best_return is not None else float("-inf")
        rows.append((metric.symbol, best_period, best_return, trend_value, return_value))

    strongest = max(rows, key=lambda item: (item[3], item[4]))
    weakest = min(rows, key=lambda item: (item[3], item[4]))

    strongest_return = strongest[2] if strongest[2] is not None else 0.0
    weakest_return = weakest[2] if weakest[2] is not None else 0.0
    return (
        f"Strongest relative trend: {strongest[0]} (trend score {strongest[3]:.2f}, best period {strongest[1]} at {strongest_return:.2f}%). "
        f"Weakest relative trend: {weakest[0]} (trend score {weakest[3]:.2f}, best period {weakest[1]} at {weakest_return:.2f}%)."
    )


def recommend_top_join_stocks(metrics: list[StockMetrics], top_n: int = 10) -> list[tuple[str, float, str]]:
    """Rank near-term join candidates using momentum, trend, and risk penalties.

    Returns tuples: (symbol, score, rationale)
    """
    if not metrics or top_n <= 0:
        return []

    rows = []
    for item in metrics:
        r1 = item.returns.get("1mo")
        r3 = item.returns.get("3mo")
        r6 = item.returns.get("6mo")
        momentum = (
            (r1 if r1 is not None else 0.0) * 0.4
            + (r3 if r3 is not None else 0.0) * 0.4
            + (r6 if r6 is not None else 0.0) * 0.2
        )
        trend = item.trend_score if item.trend_score is not None else 0.0
        volatility = item.volatility_30d if item.volatility_30d is not None else 40.0
        drawdown = abs(item.max_drawdown_1y) if item.max_drawdown_1y is not None else 30.0
        risk = volatility * 0.6 + drawdown * 0.4
        rows.append(
            {
                "symbol": item.symbol,
                "momentum": momentum,
                "trend": trend,
                "risk": risk,
                "r1": r1,
                "r3": r3,
            }
        )

    if not rows:
        return []

    momentum_mean = sum(row["momentum"] for row in rows) / len(rows)
    trend_mean = sum(row["trend"] for row in rows) / len(rows)
    risk_mean = sum(row["risk"] for row in rows) / len(rows)

    def _std(values: list[float], mean: float) -> float:
        if len(values) < 2:
            return 1.0
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return math.sqrt(variance) if variance > 1e-9 else 1.0

    momentum_std = _std([row["momentum"] for row in rows], momentum_mean)
    trend_std = _std([row["trend"] for row in rows], trend_mean)
    risk_std = _std([row["risk"] for row in rows], risk_mean)

    ranked: list[tuple[str, float, str]] = []
    for row in rows:
        momentum_z = (row["momentum"] - momentum_mean) / momentum_std
        trend_z = (row["trend"] - trend_mean) / trend_std
        risk_z = (row["risk"] - risk_mean) / risk_std
        positive_signal_bonus = 0.0
        if row["r1"] is not None and row["r1"] > 0:
            positive_signal_bonus += 0.15
        if row["r3"] is not None and row["r3"] > 0:
            positive_signal_bonus += 0.15

        score = 0.55 * momentum_z + 0.30 * trend_z - 0.35 * risk_z + positive_signal_bonus
        rationale = (
            f"momentum={row['momentum']:.2f}, trend={row['trend']:.2f}, "
            f"risk={row['risk']:.2f}, bonus={positive_signal_bonus:.2f}"
        )
        ranked.append((row["symbol"], round(score, 4), rationale))

    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:top_n]


def analyze_sector_groups(
    metrics: list[StockMetrics],
    sector_by_symbol: dict[str, str],
    periods: list[str] | None = None,
    top_n: int = 3,
) -> dict[str, dict[str, list[tuple[str, float, int]]]]:
    target_periods = periods or ["3mo", "6mo", "1y"]

    sector_rows: dict[str, list[StockMetrics]] = {}
    for metric in metrics:
        sector = sector_by_symbol.get(metric.symbol, "unknown")
        sector_rows.setdefault(sector, []).append(metric)

    sector_stats: dict[str, dict[str, float | int]] = {}
    for sector, items in sector_rows.items():
        vol_values = [item.volatility_30d for item in items if item.volatility_30d is not None]
        avg_vol = sum(vol_values) / len(vol_values) if vol_values else 40.0

        period_avg: dict[str, float] = {}
        positive_count = 0
        total_count = 0
        for period in ["3mo", "6mo", "1y"]:
            values = [item.returns.get(period) for item in items if item.returns.get(period) is not None]
            if values:
                period_avg[period] = sum(values) / len(values)
                positive_count += sum(1 for value in values if value > 0)
                total_count += len(values)

        consistency = (positive_count / total_count) if total_count else 0.0
        sustainable_base = (
            period_avg.get("3mo", 0.0) * 0.35
            + period_avg.get("6mo", 0.0) * 0.35
            + period_avg.get("1y", 0.0) * 0.30
            - avg_vol * 0.15
            + consistency * 10.0
        )

        sector_stats[sector] = {
            "count": len(items),
            "volatility": avg_vol,
            "consistency": consistency,
            "sustainable_base": sustainable_base,
            "3mo": period_avg.get("3mo", 0.0),
            "6mo": period_avg.get("6mo", 0.0),
            "1y": period_avg.get("1y", 0.0),
        }

    output: dict[str, dict[str, list[tuple[str, float, int]]]] = {}
    for period in target_periods:
        growth_ranking = sorted(
            [
                (sector, stats[period], int(stats["count"]))
                for sector, stats in sector_stats.items()
            ],
            key=lambda row: row[1],
            reverse=True,
        )

        pillar_ranking = sorted(
            [
                (
                    sector,
                    (stats[period] * 0.45 + stats["count"] * 0.35 - stats["volatility"] * 0.20),
                    int(stats["count"]),
                )
                for sector, stats in sector_stats.items()
            ],
            key=lambda row: row[1],
            reverse=True,
        )

        sustainable_ranking = sorted(
            [
                (
                    sector,
                    (stats["sustainable_base"] * 0.80 + stats[period] * 0.20),
                    int(stats["count"]),
                )
                for sector, stats in sector_stats.items()
            ],
            key=lambda row: row[1],
            reverse=True,
        )

        output[period] = {
            "pillar": [(sector, round(score, 2), count) for sector, score, count in pillar_ranking[:top_n]],
            "growth": [(sector, round(score, 2), count) for sector, score, count in growth_ranking[:top_n]],
            "sustainable": [(sector, round(score, 2), count) for sector, score, count in sustainable_ranking[:top_n]],
        }
    return output
