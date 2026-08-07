# Crypto Analyzer — Architecture Document

## Overview

A standalone Python tool for cryptocurrency technical analysis using SMA crossover strategy. Fetches OHLCV data from the Toobit exchange, computes indicators (SMA, RSI, MACD, Bollinger Bands), generates buy/sell signals, and sends notifications to a Bale bot. Supports continuous monitoring mode for server deployment.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11 |
| Data Source | CCXT (Toobit exchange, free, no API key) |
| Data Processing | pandas |
| Charting | TradingView Lightweight Charts v4.1.3 (CDN) |
| Notifications | Bale Bot API (`tapi.bale.ai`) |
| UI Language | Persian (Farsi), RTL |
| Output | Standalone HTML + CSV files + Bale notifications |

---

## Project Structure

```
crypto-analyzer/
├── main.py                    # Entry point — orchestrates pipeline + monitor mode
├── config.py                  # Central configuration (symbols, timeframes, paths, Bale)
├── fetch_data.py              # OHLCV data fetcher via CCXT (Toobit)
├── analyze.py                 # Technical analysis engine (SMA, RSI, MACD, Bollinger, signals)
├── generate_chart.py          # Interactive HTML chart generator (TradingView)
├── notifier.py                # Bale bot notification module
├── requirements.txt           # Python dependencies
│
├── data/
│   └── all_data.json          # Combined multi-timeframe data for chart
│
├── {SYMBOL}_{TIMEFRAME}.csv   # OHLCV data per symbol per timeframe
├── chart.html                 # Generated interactive chart (standalone)
│
├── fix_analyze.py             # Dev utility (older signal logic)
├── check_fi                   # Dev utility (diagnostic)
├── a                          # Dev utility (older analyze.py)
└── __pycache__/               # Compiled Python bytecode
```

---

## Module Details

### `config.py` — Configuration

Central configuration using `pathlib.Path` for OS-independent paths.

```python
# Exchange
EXCHANGE_NAME = "toobit"

# Symbols
SYMBOLS = ["BTC/USDT", "ETH/USDT", "WLD/USDT", "NEAR/USDT", "DOGE/USDT"]

# Timeframes
TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]
TIMEFRAME = "1h"  # default for console output

# Data
LIMIT = 500  # candles per fetch

# Output files
CHART_FILE = BASE_DIR / "chart.html"
ALL_DATA_FILE = DATA_DIR / "all_data.json"

# Bale Bot
BALE_TOKEN = "..."
BALE_CHAT_ID = "..."
BALE_ENABLED = True

# Monitoring intervals
MONITOR_CONFIG = {
    "1h":  {"interval": 30, "unit": "min"},
    "15m": {"interval": 15, "unit": "min"},
    "4h":  {"interval": 240, "unit": "min"},
    "1d":  {"interval": 1440, "unit": "min"},
}
```

---

### `fetch_data.py` — Data Fetcher

Handles communication with Toobit exchange via CCXT.

```
get_ohlcv(symbol, timeframe, limit) -> DataFrame
    Returns: [timestamp, open, high, low, close, volume]

fetch_all(symbols, timeframe, limit) -> dict[symbol -> DataFrame]

fetch_all_timeframes(symbols, timeframes) -> dict[timeframe -> dict[symbol -> DataFrame]]
```

---

### `analyze.py` — Technical Analysis Engine

Implements indicators and signal generation.

#### Indicators

| Function | Description | Columns Added |
|----------|-------------|---------------|
| `add_sma(df, window)` | Simple Moving Average | `sma_{window}` |
| `add_rsi(df, period=14)` | Relative Strength Index | `rsi` |
| `add_macd(df, 12, 26, 9)` | MACD Line + Signal + Histogram | `macd_line`, `macd_signal`, `macd_histogram` |
| `add_bollinger(df, 20, 2.0)` | Bollinger Bands | `bb_upper`, `bb_middle`, `bb_lower` |
| `add_all_indicators(df)` | Applies all indicators | All above |

#### Signal Logic (SMA 9/36 Crossover)

```
BUY  = SMA9 crosses ABOVE SMA36 AND close > both SMAs
SELL = SMA9 crosses BELOW SMA36 AND close < both SMAs
```

Only triggered on confirmed candle close (no repainting).

```python
add_signals(df, symbol="", notify=False) -> DataFrame
    Adds "signal" column: "buy" | "sell" | None
    If notify=True, sends new signal to Bale
```

#### Console Output

```
analyze_symbol(df, symbol) -> None
    Prints: price, change %, SMA, RSI, MACD, Bollinger, signals, volume, high/low

analyze_all(data) -> None
    Iterates all symbols
```

---

### `generate_chart.py` — Chart Generator

Produces standalone interactive HTML chart with TradingView Lightweight Charts.

#### Features
- Candlestick chart (green/red)
- SMA-9 (indigo) + SMA-36 (purple) overlays — toggleable
- Bollinger Bands (3 lines) — toggleable
- RSI panel (with 30/50/70 reference lines) — toggleable
- MACD panel (line + signal + histogram) — toggleable
- Volume histogram — toggleable
- Buy/sell signal markers (arrows)
- Timeframe selector dropdown
- RTL Persian UI (Vazirmatn font)
- Interactive crosshair tooltips

```python
build_chart_html(analyzed, chart_file) -> str
    Returns path to generated HTML file

open_chart(chart_file) -> None
    Opens in default browser
```

---

### `notifier.py` — Bale Bot Notifications

Sends formatted signal messages to Bale messenger.

```python
send_to_bale(text) -> dict | None
    POST to https://tapi.bale.ai/bot{TOKEN}/sendMessage

send_signal(symbol, signal_type, price, timestamp,
            rsi=None, macd_hist=None,
            bb_upper=None, bb_lower=None,
            sma9=None, sma36=None) -> dict | None
    Formats and sends signal message with all indicators
```

#### Message Format Example
```
🟢 **سیگنال خرید (BUY)**

ارز: BTC/USDT
قیمت: 64,872.82 USDT
زمان: 2026-08-07 14:30:00

استراتژی: تقاطع SMA9 / SMA36
SMA9: 64,469.22 | SMA36: 64,561.71
RSI (14): 69.0 (خنثی)
MACD Histogram: 37.09 (صعودی)
Bollinger: بالا 64,846.61 | پایین 64,095.08

تحلیل کریپتو | صرافی: toobit
```

---

### `main.py` — Entry Point / Orchestrator

Two modes of operation:

#### Mode 1: Once (`--mode once`)
```
1. Fetch data for all timeframes
2. Add indicators (SMA, RSI, MACD, Bollinger)
3. Generate signals (SMA 9/36 crossover)
4. Print console analysis
5. Save CSV files
6. Generate HTML chart
7. Open chart in browser
8. Send signals to Bale (if new)
```

#### Mode 2: Monitor (`--mode monitor`) — For Server
```
Loop:
  1. Check which timeframes are due (based on MONITOR_CONFIG)
  2. Fetch only those timeframes
  3. Add indicators + signals
  4. If NEW signal detected -> send to Bale
  5. If duplicate -> skip
  6. Sleep 30 seconds
```

#### CLI Arguments
```
--mode {once,monitor}     Execution mode (default: once)
--no-chart               Don't open chart browser (for server)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Toobit Exchange                          │
│                     (CCXT — No API Key)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ OHLCV Bars
                           ▼
                  ┌─────────────────┐
                  │  fetch_data.py  │
                  │  get_ohlcv()    │
                  └────────┬────────┘
                           │ pd.DataFrame
                           ▼
                  ┌─────────────────┐
                  │    main.py      │
                  │  (Orchestrator) │
                  └────┬───────┬────┘
                       │       │
          ┌────────────┘       └────────────┐
          ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│   analyze.py     │              │ generate_chart.py│
│                  │              │                  │
│  • SMA-9, SMA-36 │              │  • Candlesticks  │
│  • RSI (14)      │              │  • SMA overlays  │
│  • MACD (12,26,9)│              │  • BB bands      │
│  • Bollinger(20) │              │  • RSI panel     │
│  • Buy/Sell      │              │  • MACD panel    │
│    Signals       │              │  • Volume        │
│                  │              │  • Signal arrows │
└───────┬──────────┘              └────────┬─────────┘
        │                                  │
        ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐
│   notifier.py    │              │   chart.html     │
│                  │              │   (standalone    │
│  • Bale API      │              │    interactive)  │
│  • Format msg    │              └──────────────────┘
│  • Send alert    │
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│   Bale Messenger │
│   (User Bot)     │
└──────────────────┘
```

---

## Monitoring Logic

### Timeframe Check Intervals

| Timeframe | Check Every | Reason |
|-----------|-------------|--------|
| 15m | 15 minutes | New candle every 15 min |
| 1h | 30 minutes | Check mid-candle for early detection |
| 4h | 4 hours | Matches candle interval |
| 1d | 24 hours | Once per day |

### Signal Deduplication

```python
last_signals = {}  # { "BTC/USDT_1h": "sell_2026-08-06 19:00:00" }

# Only send if:
if key not in last_signals or last_signals[key] != signal_key:
    last_signals[key] = signal_key
    notifier.send_signal(...)
```

Prevents spamming the same signal on every check cycle.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Toobit exchange** | Free public API, no key required, accessible in Iran |
| **SMA 9/36 crossover** | Classic trend-following, responsive yet noise-resistant |
| **Close-price confirmation** | Reduces false signals — requires price to confirm direction |
| **Bale messenger** | Popular in Iran, free bot API |
| **`tapi.bale.ai`** | Correct API endpoint (not `api.bale.ai` which returns 503) |
| **Standalone HTML** | No server needed, portable, shareable |
| **CDN for charts** | No npm/build step required |
| **Deduplication** | Only sends NEW signals, never repeats |

---

## Dependencies

### Python Packages

| Package | Source | Purpose |
|---------|--------|---------|
| `ccxt` | pip | Exchange data fetching |
| `pandas` | pip | DataFrame operations, indicators |
| `requests` | pip | HTTP calls to Bale API |

### Browser (CDN)

| Library | Version | Purpose |
|---------|---------|---------|
| `lightweight-charts` | 4.1.3 | Interactive financial charting |
| `Vazirmatn` | Google Fonts | Persian UI typography |

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# One-time analysis (opens chart in browser)
python main.py

# One-time, no chart (server/CI)
python main.py --mode once --no-chart

# Continuous monitoring (for server)
python main.py --mode monitor
```

---

## Configuration Guide

| Want to Change | What to Edit |
|----------------|--------------|
| Add/remove coins | `SYMBOLS` list in `config.py` |
| Change monitoring intervals | `MONITOR_CONFIG` in `config.py` |
| Disable notifications | `BALE_ENABLED = False` in `config.py` |
| Change Bale bot | `BALE_TOKEN` and `BALE_CHAT_ID` in `config.py` |
| More/fewer candles | `LIMIT` in `config.py` |
| Add new indicator | Create function in `analyze.py`, add to `add_all_indicators()` |

---

## Extension Points

| Area | How to Extend |
|------|---------------|
| **New Indicator** | Add function in `analyze.py`, call from `add_all_indicators()` |
| **New Signal Type** | Add logic in `add_signals()` |
| **Different Notifier** | Create new module like `notifier.py` (e.g., email, SMS) |
| **Chart Element** | Add series in `build_chart_html()` JS template |
| **Export Format** | Add function in `fetch_data.py` (e.g., `save_to_parquet()`) |

---

## File Dependency Graph

```
config.py ← (imported by all modules)
    ↑
fetch_data.py ← (imported by main.py)
    ↑
analyze.py ← (imported by main.py)
    ↑
generate_chart.py ← (imported by main.py)
    ↑
notifier.py ← (imported by analyze.py and main.py)
    ↑
main.py (entry point — imports all above)
```

---

## Known Limitations

- No test suite — manual verification only
- No virtual environment configuration
- Single exchange (Toobit) — no fallback
- Chart HTML size grows with data
- Bale API may return 503 under heavy load
- Signal logic only uses SMA crossover (could combine with RSI/MACD for stronger signals)
