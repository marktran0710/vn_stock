from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import PERIOD_TO_DAYS


def period_to_history_window(periods: list[str]) -> str:
    max_days = max(PERIOD_TO_DAYS.get(period, 365) for period in periods)
    if max_days <= 365:
        return "2y"
    if max_days <= 365 * 2:
        return "3y"
    if max_days <= 365 * 3:
        return "5y"
    return "max"


def load_history(symbol: str, periods: list[str]) -> pd.DataFrame:
    window = period_to_history_window(periods)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=window, interval="1d", auto_adjust=True, raise_errors=False)
    if data is None or data.empty:
        raise ValueError(f"No price history returned for {symbol}")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [column[0] for column in data.columns]
    data = data.rename(columns={column: column.title() for column in data.columns})
    if "Close" not in data.columns:
        raise ValueError(f"Close price unavailable for {symbol}")
    data = data.dropna(subset=["Close"]).copy()
    data.index = pd.to_datetime(data.index)
    return data


def align_series(history: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for symbol, data in history.items():
        frames.append(data[["Close"]].rename(columns={"Close": symbol}))
    combined = pd.concat(frames, axis=1, join="outer").sort_index()
    return combined.dropna(how="all")


def load_universe_symbols(path: Path, limit: int | None = None) -> list[str]:
    universe_df = load_universe_dataframe(path, limit=limit)
    return universe_df["symbol"].tolist()


def load_universe_dataframe(path: Path, limit: int | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Universe file not found: {path}")
    df = pd.read_csv(path)
    if "symbol" not in df.columns:
        raise ValueError(f"Universe file must contain 'symbol' column: {path}")
    if "notes" not in df.columns:
        df["notes"] = "unknown"

    df = df.copy()
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["notes"] = df["notes"].astype(str).str.strip().str.lower()
    df = df[df["symbol"] != ""]
    df = df.drop_duplicates(subset=["symbol"], keep="first")

    excluded_file = Path("data/universe/excluded_symbols.txt")
    if excluded_file.exists():
        excluded_symbols = {
            line.strip().upper()
            for line in excluded_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        df = df[~df["symbol"].isin(excluded_symbols)]
    if limit is not None:
        df = df.head(limit)
    return df[["symbol", "notes"]].reset_index(drop=True)
