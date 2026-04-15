from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class StockMetrics:
    symbol: str
    latest_close: float | None
    returns: dict[str, float | None]
    volatility_30d: float | None
    max_drawdown_1y: float | None
    trend_score: float | None
    relative_strength_1y: float | None


@dataclasses.dataclass
class AnalysisResult:
    as_of: str
    benchmark: str | None
    symbols: list[str]
    metrics: list[StockMetrics]
    market_fluctuation_summary: str
    comparison_summary: str
    notes: list[str]


@dataclasses.dataclass
class UniverseScanResult:
    as_of: str
    benchmark: str | None
    total_symbols: int
    analyzed_symbols: int
    average_returns: dict[str, float]
    top_gainers_3m: list[tuple[str, float]]
    top_losers_3m: list[tuple[str, float]]
    top_join_candidates_now: list[tuple[str, float, str]]
    market_fluctuation_summary: str
    notes: list[str]
    sector_group_analysis: dict[str, dict[str, list[tuple[str, float, int]]]] = dataclasses.field(default_factory=dict)
