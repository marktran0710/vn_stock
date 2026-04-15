# VNStock Analyzer

A maintainable VN stock analysis project with two workflows:

- Compare 2-3 symbols across 1/2/3/6 months and multi-year periods
- Scan the Top 200 VN stock universe for broad market fluctuation signals

## Folder Structure

- `src/vnstock_analyzer/`: core package modules (analytics, data, reporting, CLI)
- `data/universe/top200_vn_stocks.csv`: maintained default Top 200 symbol universe
- `data/universe/excluded_symbols.txt`: symbols to skip when Yahoo data is repeatedly unavailable
- `vn_stock_analyzer.py`: compatibility entry script
- `requirements.txt`: runtime dependencies

## Install

```bash
pip install -r requirements.txt
```

## Run the UI

```bash
streamlit run ui/streamlit_app.py
```

## Compare 2-3 stocks

```bash
python vn_stock_analyzer.py VCB.VN FPT.VN MWG.VN --periods 1mo 2mo 3mo 6mo 1y 2y 3y --plot
```

## Scan Top 200 universe

```bash
python vn_stock_analyzer.py --market-scan --scan-limit 200 --output market_scan.json
```

Top join candidates are included in market-scan output by default. You can control count with `--top-n`:

```bash
python vn_stock_analyzer.py --market-scan --scan-limit 200 --top-n 10 --periods 1mo 3mo 6mo
```

## Update the Top 200 list

Edit `data/universe/top200_vn_stocks.csv`:

- Keep column `symbol`
- Use Yahoo format (for example `VCB.VN`)
- Keep one symbol per row and maintain unique symbols

If a symbol is repeatedly unavailable from Yahoo, add it to `data/universe/excluded_symbols.txt` so market-scan mode skips it.
