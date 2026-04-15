# VN Stock Analyzer

A maintainable Vietnam stock analysis platform with interactive dashboard and command-line tools. Analyze stock performance, identify top join candidates, and explore sector group analysis across multiple time windows.

**Key Features:**

- 📊 **Sector-group Analysis**: Classify sectors as pillar, growth, or sustainable across 3M/6M/12M periods
- 🎯 **Top Join Candidates**: Ranking system based on momentum, trend, and risk metrics
- 📈 **Interactive Dashboard**: Streamlit UI with market scan and stock comparison modes
- 🔍 **Universe Scanning**: Analyze top 200 VN stocks with smart caching (10-min TTL)
- 📉 **Normalized Charts**: Compare 2-3 stocks with baseline 100 normalization
- 💾 **JSON Export**: Export analysis results for integration with other tools

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or conda package manager

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/marktran0710/vn_stock.git
   cd vn_stock
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start

### Run the Interactive Dashboard (Recommended)

```bash
streamlit run ui/streamlit_app.py
```

The dashboard will open at `http://localhost:8501` with:

- **Market Scan** mode (default): Top 10 join candidates, sector group analysis (pillar/growth/sustainable), winners/losers
- **Compare** mode: Analyze 2-3 symbols side-by-side with normalized charts and metrics
- Adjustable timeframes (3M/6M/12M)
- JSON export functionality

---

## CLI Usage

### Compare 2-3 Stocks

Analyze specific symbols across multiple periods:

```bash
python vn_stock_analyzer.py VCB.VN FPT.VN MWG.VN --periods 1mo 3mo 6mo 1y 2y --plot
```

**Options:**

- `--periods`: Time windows (1mo, 3mo, 6mo, 1y, 2y, 3y)
- `--benchmark`: Reference symbol for relative performance (default: VNIndex)
- `--plot`: Generate matplotlib comparison chart (saved as `plot_comparison.png`)
- `--output`: JSON output file path

### Market Scan (Universe Analysis)

Scan the top 200 VN stocks and identify top candidates:

```bash
python vn_stock_analyzer.py --market-scan \
  --scan-limit 200 \
  --periods 1mo 3mo 6mo 1y \
  --top-n 10 \
  --output market_scan.json
```

**Options:**

- `--scan-limit`: Number of stocks to analyze (default: 50, max: 200)
- `--periods`: Analysis windows (default: 3mo 6mo 1y)
- `--top-n`: Top candidates to display (default: 10)
- `--universe-file`: Custom stock list (default: data/universe/top200_vn_stocks.csv)
- `--benchmark`: Reference index
- `--output`: JSON export path

**Example Output:**

```
Market Scan Summary (50 symbols analyzed):
Dashboard at 2026-04-15 14:30:00 UTC

Top Join Candidates (Now):
1. FPT.VN      Score: 68.45  (strength: momentum trending up, relative strength high)
2. BID.VN      Score: 65.23  (momentum Z-score: +1.2, trend: positive)
3. VCB.VN      Score: 62.88  (consistent performance)

Sector Group Analysis (3M / 6M / 12M):
- 3mo
  pillar: utilities (-1.62, n=12), banking (-3.40, n=18)
  growth: utilities (1.61, n=12), energy (0.60, n=10)
  sustainable: energy (17.56, n=10), real_estate (8.06, n=10)
```

---

## Project Structure

```
vn_stock/
├── ui/
│   └── streamlit_app.py         # Interactive dashboard
├── src/vnstock_analyzer/
│   ├── __init__.py
│   ├── analytics.py             # Core metrics and ranking algorithms
│   ├── data.py                  # Yahoo Finance data loading
│   ├── models.py                # Data class definitions
│   ├── services.py              # Reusable analysis service layer
│   ├── cli.py                   # Command-line interface
│   ├── reporting.py             # Result rendering (text/JSON)
│   └── config.py                # Configuration constants
├── data/universe/
│   ├── top200_vn_stocks.csv     # Maintained stock universe list
│   └── excluded_symbols.txt     # Symbols to skip (Yahoo unavailable)
├── scripts/
│   └── validate_universe.py     # Validate stock list integrity
├── vn_stock_analyzer.py         # Main entry point
├── requirements.txt             # Python dependencies
└── README.md
```

---

## Configuration

### Update the Stock Universe

Edit `data/universe/top200_vn_stocks.csv`:

- **Format**: CSV with columns `symbol` (required) and optional `notes` (sector metadata)
- **Symbol Format**: Yahoo Finance format (e.g., `VCB.VN`, `FPT.VN`)
- **One symbol per row**, unique symbols only

Example:

```csv
symbol,notes
VCB.VN,banking
FPT.VN,unknown
MWG.VN,retail
```

### Exclude Unavailable Symbols

If a symbol is repeatedly unavailable from Yahoo Finance, add it to `data/universe/excluded_symbols.txt`:

```
VGS.VN
MPC.VN
```

The market-scan mode will skip these symbols silently.

### Analysis Parameters

Edit `src/vnstock_analyzer/config.py` to adjust:

- Risk-free rate for return calculations
- Volatility windows (30-day, 1-year)
- Z-score thresholds for rankings
- Sector group definitions (pillar/growth/sustainable)

---

## Scoring Models

### Top Join Candidates (Composite Score)

Formula: `55% * momentum_zscore + 30% * trend_zscore - 35% * risk_zscore + bonuses`

- **Momentum**: 40% 1M + 40% 3M + 20% 6M returns (Z-scored)
- **Trend**: 1Y trend direction strength (Z-scored)
- **Risk**: 60% volatility (annualized) + 40% max drawdown (Z-scored, negative)
- **Bonuses**: +0.15–0.30 for positive signals (e.g., recent strength)

### Sector Group Classification

- **Pillar**: 45% period return + 35% coverage (count) − 20% volatility
  - Stable, large-cap focus
- **Growth**: Pure period return ranking
  - Highest performers regardless of volatility
- **Sustainable**: 80% baseline (momentum + consistency − volatility) + 20% period return
  - Risk-adjusted, consistent performers

---

## Troubleshooting

### Streamlit Dashboard Won't Start

```bash
# Clear cache and restart
rm -rf ~/.streamlit/cache/*
streamlit run ui/streamlit_app.py --logger.level=debug
```

### AttributeError with sector_group_analysis

**Cause**: Stale Streamlit cache
**Solution**: Clear browser cache and Streamlit cache, restart app

### Yahoo Finance Download Errors

**Common Symbols**: VGS.VN, MPC.VN fail intermittently
**Solution**: Add to `data/universe/excluded_symbols.txt`

### Port Already in Use

```bash
# Use a different port
streamlit run ui/streamlit_app.py --server.port 8505
```

---

## Development

### Run Tests

```bash
python -m py_compile src/vnstock_analyzer/*.py ui/streamlit_app.py
```

### Validate Stock Universe

```bash
python scripts/validate_universe.py
```

### Code Style

- Follow PEP 8 conventions
- Use type hints where practical
- English-only comments and docstrings (per `.github/instructions/english-only.instructions.md`)

---

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes with clear messages (`git commit -m 'feat: description'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## Support

For issues or questions, please open a GitHub issue at: https://github.com/marktran0710/vn_stock/issues
