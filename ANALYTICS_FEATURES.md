# Advanced Analytics Features

This document describes the new analytics functions integrated from `vnstock` and `pandas_ta` libraries.

## Overview

The VN Stock Analyzer now includes comprehensive analytics capabilities:

- **Historical Data**: Fetch stock historical data (OHLCV)
- **Financial Ratios**: Get fundamental metrics (P/E, ROE, ROA, Debt/Equity, etc.)
- **Peer Comparison**: Compare a stock with sector peers
- **Technical Indicators**: Calculate SMA (20, 50, 200) and RSI (14)
- **Real-Time Prices**: Get current stock prices and market board data

## CLI Usage

### 1. Stock Details (All-in-One)

Fetch comprehensive stock details including financial ratios, technical indicators, and real-time price:

```bash
python vn_stock_analyzer.py VCB.VN --details
python vn_stock_analyzer.py VCB.VN --details --output stock_details.json
```

**Output includes:**
- Real-time price
- Financial ratios
- Technical indicators (SMA 20/50/200, RSI 14)

### 2. Financial Ratios

Fetch financial metrics for fundamental analysis:

```bash
python vn_stock_analyzer.py VCB.VN --financials
python vn_stock_analyzer.py FPT.VN --financials --output financials.json
```

**Metrics returned:**
- P/E Ratio (Price-to-Earnings)
- ROE (Return on Equity)
- ROA (Return on Assets)
- Debt/Equity Ratio
- Current Ratio
- QuickRatio
- Asset Turnover
- And more...

### 3. Technical Analysis

Calculate technical indicators for trend analysis:

```bash
python vn_stock_analyzer.py VCB.VN --technicals
python vn_stock_analyzer.py VCB.VN --technicals --output technicals.json
```

**Indicators calculated:**
- SMA (Simple Moving Average) 20-day
- SMA 50-day
- SMA 200-day
- RSI (Relative Strength Index) 14-period

### 4. Real-Time Prices

Fetch current stock prices from the market board:

```bash
python vn_stock_analyzer.py VCB.VN --realtime
python vn_stock_analyzer.py VCB.VN --realtime --output realtime.json
```

**Data includes:**
- Current price
- Bid price
- Ask price
- Volume
- Price change
- Change percentage

### 5. Peer Comparison

Compare a stock's metrics with sector peers:

```bash
# Compare P/E ratio with peers (default)
python vn_stock_analyzer.py VCB.VN --peers

# Compare ROE with peers
python vn_stock_analyzer.py VCB.VN --peers --metric "ROE"

# Other metrics: ROA, Debt/Equity, Current Ratio, etc.
python vn_stock_analyzer.py VCB.VN --peers --metric "ROA" --output peer_comparison.json
```

## Python API Usage

### Import Analytics Functions

```python
from src.vnstock_analyzer.analytics import (
    get_stock_historical_data,
    get_financial_ratios,
    get_peer_comparison,
    calculate_technical_indicators,
    get_realtime_price,
)

from src.vnstock_analyzer.services import (
    get_stock_details,
    get_sector_peers,
)
```

### Example: Get Stock Details

```python
from src.vnstock_analyzer.services import get_stock_details

details = get_stock_details("VCB.VN")

# Access real-time price
price = details["realtime_price"]
print(f"Current price: {price['price']}")

# Access financial ratios
ratios = details["financial_ratios"]
print(f"P/E Ratio: {ratios.get('P/E', 'N/A')}")

# Access technical indicators
indicators = details["technical_indicators"]
if indicators:
    for name, series in indicators.items():
        latest = series.iloc[-1]
        print(f"{name}: {latest:.2f}")
```

### Example: Calculate Technical Indicators

```python
from src.vnstock_analyzer.analytics import (
    get_stock_historical_data,
    calculate_technical_indicators,
)

# Fetch historical data
history = get_stock_historical_data("VCB.VN")

# Calculate indicators with custom SMA periods
indicators = calculate_technical_indicators(
    history,
    sma_periods=[10, 20, 50, 200]
)

# Display results
for name, series in indicators.items():
    print(f"{name}: {series.iloc[-1]:.2f}")
```

### Example: Peer Comparison

```python
from src.vnstock_analyzer.services import get_sector_peers

# Compare with peers on ROE metric
comparison = get_sector_peers("VCB.VN", metric="ROE")

# Get own ratios
own_roe = comparison["own_ratios"]["ROE"]

# Get peer comparison data
peers = comparison["peer_comparison"]
print(f"Own ROE: {own_roe}")
print(f"Peer comparison: {peers}")
```

## Dependencies

Required packages (automatically installed):

```
vnstock>=0.3          # Vietnamese stock data
pandas_ta>=0.3.14b    # Technical analysis indicators
```

## Data Sources

- **YahooFinance** (via vnstock): Historical OHLCV data
- **HSX/HNX API** (via vnstock): Financial ratios, real-time prices
- **Computed**: Technical indicators using pandas_ta

## Error Handling

All functions gracefully handle data unavailability:

- Returns `None` if data cannot be fetched
- Prints error messages to console
- Upstream code uses defensive `getattr()` and null checks

Example:

```python
ratios = get_financial_ratios("INVALID.VN")
if ratios is None:
    print("Financial data unavailable for this symbol")
```

## Performance Notes

- Real-time data calls: ~1-2 seconds per symbol
- Financial ratio calls: ~1-2 seconds per symbol
- Technical indicator calculation: ~100-500ms per symbol (depends on data length)
- Historical data fetching: ~1-3 seconds per symbol

For batch operations, consider:
1. Implementing rate limiting
2. Using concurrent.futures for parallel requests
3. Caching results with 10-60 minute TTL

## Troubleshooting

### "vnstock is None" error

**Cause**: vnstock library not installed
**Solution**: `pip install vnstock`

### "pandas_ta is None" error

**Cause**: pandas_ta library not installed
**Solution**: `pip install pandas_ta`

### Empty results from financial_ratio()

**Cause**: Symbol not found in HSX/HNX database
**Solution**: Verify symbol format (e.g., VCB.VN) and availability

### Technical indicators all NaN

**Cause**: Insufficient historical data (need at least 200 data points for 200-day SMA)
**Solution**: Use symbols with longer trading history or reduce SMA periods

## Future Enhancements

- [ ] Add Bollinger Bands (BB) from pandas_ta
- [ ] Add MACD (Moving Average Convergence Divergence)
- [ ] Add Stochastic Oscillator
- [ ] Implement caching for financial ratios (changes daily)
- [ ] Add price alert thresholds
- [ ] Implement portfolio-level analytics
