# Crypto Analyzer — Architecture Document

## Overview

A standalone Python tool for cryptocurrency technical analysis using SMA crossover strategy. Fetches OHLCV data from the Toobit exchange, computes indicators (SMA, RSI, MACD, Bollinger Bands), generates buy/sell signals, and sends notifications with chart screenshots to a Bale bot. Supports continuous monitoring mode for server deployment.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11 |
| Data Source | CCXT (Toobit exchange, free, no API key) |
| Data Processing | pandas |
| Charting | TradingView Lightweight Charts v4.1.3 (CDN) |
| Chart Screenshot | html2image + Microsoft Edge (headless) |
| Notifications | Bale Bot API (`tapi.bale.ai`) |
| UI Language | Persian (Farsi), RTL |
| Output | Standalone HTML + CSV files + Bale notifications |
| Deployment | Docker / Railway / systemd |

---

## Project Structure

```
crypto-analyzer/
├── main.py                    # Entry point — orchestrates pipeline + monitor mode
├── config.py                  # Central configuration (env vars, symbols, timeframes)
├── fetch_data.py              # OHLCV data fetcher via CCXT (Toobit)
├── analyze.py                 # Technical analysis engine (SMA, RSI, MACD, Bollinger, signals)
├── generate_chart.py          # Interactive HTML chart generator (TradingView)
├── notifier.py                # Bale bot notification module (text + photo)
├── chart_screenshot.py        # Chart screenshot via html2image + Edge
├── requirements.txt           # Python dependencies
│
├── Dockerfile                 # Docker image with Edge browser
├── docker-compose.yml         # Docker compose for local deployment
├── railway.json               # Railway.app deployment config
├── crypto-analyzer.service    # systemd service file (alternative deployment)
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation (Persian)
├── ARCHITECT.md               # This file
│
├── data/                      # Data directory (git-ignored in production)
│   └── all_data.json          # Combined multi-timeframe data for chart
│
└── [SYMBOL]_[TIMEFRAME].csv   # OHLCV data per symbol per timeframe (git-ignored)
```

---

## Module Details

### `config.py` — Configuration

Uses environment variables loaded from `.env` file (no external dependencies).

| Constant | Default | Description |
|----------|---------|-------------|
| `EXCHANGE_NAME` | `"toobit"` | Exchange identifier for CCXT |
| `SYMBOLS` | `["BTC/USDT", "ETH/USDT", "WLD/USDT", "NEAR/USDT", "DOGE/USDT"]` | Trading pairs |
| `TIMEFRAMES` | `["5m", "15m", "1h", "4h", "1d"]` | Supported candle intervals |
| `TIMEFRAME` | `"1h"` | Default timeframe for console output |
| `LIMIT` | `500` | Max candles per fetch |
| `BALE_TOKEN` | from env | Bale bot token |
| `BALE_CHAT_ID` | from env | Bale chat ID |
| `BALE_ENABLED` | `true` | Enable/disable notifications |
| `SWING_LOOKBACK` | `20` | Candles to find last swing for Stop Loss |
| `REWARD_RISK_MULT` | `2.0` | Total reward = stop distance × mult (split into R1/R2/R3) |
| `MONITOR_CONFIG` | `{30m: 30, 1h: 60}` | Monitoring intervals (checks are clock-aligned) |

---

### `fetch_data.py` — Data Fetcher

Handles communication with Toobit exchange via CCXT.

```
get_ohlcv(symbol, timeframe, limit) -> DataFrame
    Returns: [timestamp, open, high, low, close, volume]

fetch_all(symbols, timeframe, limit) -> dict[symbol → DataFrame]

fetch_all_timeframes(symbols, timeframes) -> dict[timeframe → dict[symbol → DataFrame]]
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
| `add_all_indicators(df)` | Applies all indicators at once | All above |

#### Signal Logic (SMA 9/36 Crossover)

```
BUY  = SMA9 crosses ABOVE SMA36 AND close > both SMAs
SELL = SMA9 crosses BELOW SMA36 AND close < both SMAs
```

Only triggered on confirmed candle close (no repainting).

#### Entry / Stop Loss / Targets

Each signal also computes a risk-managed trade plan:

| Field | Buy | Sell |
|-------|-----|------|
| `entry` | close of signal candle | close of signal candle |
| `stop_loss` | last swing low before signal | last swing high before signal |
| `risk` | `entry - stop` | `stop - entry` |
| `reward` | `risk × REWARD_RISK_MULT` (2×) | same |
| `tp1` | `entry + reward/3` (R1) | `entry - reward/3` |
| `tp2` | `entry + 2×reward/3` (R2) | `entry - 2×reward/3` |
| `tp3` | `entry + reward` (R3) | `entry - reward` |

`swing_low/swing_high` are computed from the `SWING_LOOKBACK` (20) candles *before* the signal candle only — no lookahead.

```python
add_signals(df, symbol="", notify=False) -> DataFrame
    Adds "signal" column: "buy" | "sell" | None
    Also adds: entry, stop_loss, tp1, tp2, tp3
    If notify=True, sends new signal to Bale
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
open_chart(chart_file) -> None
```

---

### `notifier.py` — Bale Bot Notifications

Sends formatted signal messages with chart screenshots to Bale messenger.

```python
send_to_bale(text) -> dict | None
    POST to https://tapi.bale.ai/bot{TOKEN}/sendMessage

send_photo_to_bale(photo_bytes, caption) -> dict | None
    POST to https://tapi.bale.ai/bot{TOKEN}/sendPhoto

send_signal(symbol, signal_type, price, timestamp,
            rsi=None, macd_hist=None,
            bb_upper=None, bb_lower=None,
            sma9=None, sma36=None,
            chart_df=None, timeframe="") -> dict | None
    Formats professional signal message + sends screenshot
```

#### Signal Message Format
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 سیگنال خرید | BUY 🔼
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🪙 ارز: BTC/USDT
⏰ زمان: جمعه 16 مرداد 1405
📐 تایم‌فریم: 1h
📈 روند: صعودی

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ورود (Entry): 65,292.32
🛑 استاپ لاس (Stop Loss): 64,166.01
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 تارگت‌ها (Take Profit):
  R1: 66,043.19
  R2: 66,794.07
  R3: 67,544.94
━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ نوع سیگنال: تقاطع طلایی Golden Cross

📋 اندیکاتورها:
  • SMA9: 64,652.38 | SMA36: 64,590.18
  • RSI(14): 80.2
  • MACD Hist: 84.57
  • BB Upper: 64,850.15 | BB Lower: 64,092.07

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 صرافی: toobit
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Timestamp is converted to the Persian (Jalali) calendar, e.g. `جمعه 16 مرداد 1405`.

---

### `chart_screenshot.py` — Chart Screenshot

Uses html2image + Microsoft Edge (headless) to capture TradingView chart as PNG.

```python
take_chart_screenshot(symbol, timeframe) -> bytes | None
    Opens chart.html with ?tf= parameter
    Waits for chart to render (5s)
    Returns PNG bytes
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
8. Send new signals to Bale (if recent)
```

#### Mode 2: Monitor (`--mode monitor`) — For Server
```
Loop:
  1. Check which timeframes are due (based on MONITOR_CONFIG)
  2. Fetch only those timeframes
  3. Add indicators + signals
  4. If NEW signal detected → send to Bale + screenshot
  5. If duplicate → skip
  6. Sleep 30 seconds
```

#### CLI Arguments
```
--mode {once,monitor}     Execution mode (default: once)
--no-chart               Don't open chart browser (for server)
```

---

## Monitoring Logic

### Timeframe Check Intervals (clock-aligned)

Checks are synchronized to round clock times — right after each candle closes:

| Timeframe | Check Minutes | Reason |
|-----------|---------------|--------|
| 30m | `:01` and `:31` | 1 min after each 30m candle close |
| 1h | `:01` | 1 min after each hourly candle close |

Examples: 12:01 → 12:31 → 13:01 (30m), and 13:01 → 14:01 (1h).

### Signal Deduplication (persistent)

Signals are deduplicated across **restarts** using `data/last_signals.json` (keyed by `symbol_timeframe` → `type_timestamp`).

```python
last_signals = load_last_signals()   # from data/last_signals.json

# Only send if:
#  1. Signal is recent (within interval × 2 minutes)  → no stale signals
#  2. key not in last_signals or last_signals[key] != signal_key
if last_signals.get(key) != signal_key and is_recent(row):
    last_signals[key] = signal_key
    notifier.send_signal(...)
    save_last_signals(last_signals)
```

Prevents spamming the same signal on every check cycle AND prevents re-sending old signals after a restart (e.g. a month-old BTC/1d signal).

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
│  • Format msg    │              │    interactive)  │
│  • Send text     │              └────────┬─────────┘
│  • Send photo    │                       │
└───────┬──────────┘                       │
        │                                  ▼
        │                         ┌──────────────────┐
        │                         │chart_screenshot  │
        │                         │.py              │
        │                         │                 │
        │                         │  html2image +   │
        │                         │  Edge headless  │
        │                         └────────┬─────────┘
        │                                  │
        ▼                                  ▼
┌──────────────────────────────────────────────────┐
│                  Bale Messenger                   │
│                                                  │
│  📝 Text message  +  📸 Chart screenshot        │
└──────────────────────────────────────────────────┘
```

---

## Deployment Options

### Option 1: Docker

```bash
docker-compose up -d
```

### Option 2: Railway.app

1. Push to GitHub
2. New Project → Deploy from GitHub
3. Set environment variables
4. Auto-deploys on every commit

### Option 3: VPS with systemd

```bash
pip install -r requirements.txt
sudo cp crypto-analyzer.service /etc/systemd/system/
sudo systemctl enable --now crypto-analyzer
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BALE_TOKEN` | Bale bot token from @BotFather | `1210211811:...` |
| `BALE_CHAT_ID` | Chat ID to send messages to | `506757503` |
| `BALE_ENABLED` | Enable notifications | `true` |
| `EXCHANGE_NAME` | Exchange name | `toobit` |
| `LIMIT` | Candles per fetch | `500` |

---

## Dependencies

### Python Packages

| Package | Purpose |
|---------|---------|
| `ccxt` | Exchange data fetching |
| `pandas` | DataFrame operations, indicators |
| `matplotlib` | Fallback chart image generation |
| `requests` | HTTP calls to Bale API |
| `html2image` | Chart screenshot via browser |
| `selenium` | Browser automation (fallback) |

### Browser (Docker only)

| Browser | Purpose |
|---------|---------|
| Microsoft Edge | Headless browser for html2image |

### CDN (Browser)

| Library | Version | Purpose |
|---------|---------|---------|
| `lightweight-charts` | 4.1.3 | Interactive financial charting |
| `Vazirmatn` | Google Fonts | Persian UI typography |

---

## Extension Points

| Area | How to Extend |
|------|---------------|
| **New Indicator** | Add function in `analyze.py`, call from `add_all_indicators()` |
| **New Signal Type** | Add logic in `add_signals()` |
| **Different Notifier** | Create new module (e.g., telegram_notifier.py) |
| **Chart Element** | Add series in `build_chart_html()` JS template |
| **New Symbol** | Append to `SYMBOLS` in `config.py` |
| **New Timeframe** | Append to `TIMEFRAMES` and `MONITOR_CONFIG` |

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
chart_screenshot.py ← (imported by notifier.py)
    ↑
notifier.py ← (imported by main.py)
    ↑
main.py (entry point — imports all above)
```
