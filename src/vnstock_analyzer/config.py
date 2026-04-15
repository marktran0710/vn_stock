from __future__ import annotations

from pathlib import Path

DEFAULT_PERIODS = ["1mo", "2mo", "3mo", "6mo", "1y", "2y", "3y", "5y"]
PERIOD_TO_DAYS = {
    "1mo": 30,
    "2mo": 60,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 365 * 2,
    "3y": 365 * 3,
    "5y": 365 * 5,
}

TOP200_DEFAULT_PATH = Path("data/universe/top200_vn_stocks.csv")
