# دریافت داده OHLCV از صرافی Toobit با CCXT
import json

import ccxt
import pandas as pd

import config


def get_ohlcv(symbol: str, timeframe: str = config.TIMEFRAME, limit: int = config.LIMIT) -> pd.DataFrame:
    """دریافت داده شمعی (OHLCV) از صرافی Toobit و برگرداندن DataFrame"""
    exchange = ccxt.toobit({
        "enableRateLimit": True,
    })

    bars = exchange.fetch_ohlcv(
        symbol,
        timeframe=timeframe,
        limit=limit
    )

    df = pd.DataFrame(
        bars,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    return df


def fetch_all(symbols: list, timeframe: str = config.TIMEFRAME, limit: int = config.LIMIT) -> dict:
    """دریافت داده همه ارزها و برگرداندن دیکشنری {نماد: DataFrame}"""
    data = {}
    for symbol in symbols:
        print(f"دریافت داده {symbol} ({timeframe}) ...")
        df = get_ohlcv(symbol, timeframe, limit)
        data[symbol] = df
    return data


def fetch_all_timeframes(symbols: list = None, timeframes: list = None) -> dict:
    """دریافت داده همه ارزها برای تایم‌فریم‌های مشخص"""
    if symbols is None:
        symbols = config.SYMBOLS
    if timeframes is None:
        timeframes = config.TIMEFRAMES

    all_data = {}
    for timeframe in timeframes:
        all_data[timeframe] = fetch_all(symbols, timeframe)
    return all_data


def df_to_json(df: pd.DataFrame) -> list:
    """تبدیل DataFrame به لیست JSON برای استفاده در چارت"""
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "time": int(row["timestamp"].timestamp()),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })
    return rows


def data_to_json(all_data: dict) -> dict:
    """تبدیل ساختار داده همه تایم‌فریم‌ها به JSON"""
    result = {}
    for timeframe, symbols in all_data.items():
        result[timeframe] = {}
        for symbol, df in symbols.items():
            result[timeframe][symbol] = df_to_json(df)
    return result


def save_all_data(all_data: dict) -> str:
    """ذخیره همه داده‌ها (همه تایم‌فریم‌ها) در یک فایل JSON"""
    json_data = data_to_json(all_data)
    with open(config.ALL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(json_data, f)
    return str(config.ALL_DATA_FILE)