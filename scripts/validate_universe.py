from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def validate(path: Path, expected_count: int) -> int:
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1

    df = pd.read_csv(path)
    if "symbol" not in df.columns:
        print("ERROR: missing required column: symbol")
        return 1

    symbols = [str(item).strip().upper() for item in df["symbol"].tolist() if str(item).strip()]
    unique_symbols = list(dict.fromkeys(symbols))
    duplicate_count = len(symbols) - len(unique_symbols)

    print(f"Rows with symbols: {len(symbols)}")
    print(f"Unique symbols: {len(unique_symbols)}")
    print(f"Duplicate rows: {duplicate_count}")

    if len(unique_symbols) != expected_count:
        print(f"ERROR: expected {expected_count} unique symbols, found {len(unique_symbols)}")
        return 2

    print("Universe validation passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate VN stock universe CSV")
    parser.add_argument("--file", type=Path, default=Path("data/universe/top200_vn_stocks.csv"))
    parser.add_argument("--expected-count", type=int, default=200)
    args = parser.parse_args()
    return validate(args.file, args.expected_count)


if __name__ == "__main__":
    raise SystemExit(main())
