# تنظیمات پروژه تحلیل کریپتو
# Multi-exchange: Binance (primary) + Toobit (fallback)
import os
from pathlib import Path

# مسیر پایه پروژه (پوشه‌ای که این فایل در آن است)
BASE_DIR = Path(__file__).resolve().parent

# --- صرافی ---
# Toobit - صرافی رایگان بدون کلید API
EXCHANGE_NAME = "toobit"

# لیست ارزهای مورد نظر
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "WLD/USDT",
    "NEAR/USDT",
    "DOGE/USDT",
]

# تایم‌فریم‌های پشتیبانی‌شده
TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]

# تایم‌فریم پیش‌فرض (نمایش کنسول)
TIMEFRAME = "1h"

# --- مانیتورینگ ---
# هر تایم‌فریم هر چند دقیقه چک بشه
MONITOR_CONFIG = {
    "1h":  {"interval": 30, "unit": "min"},   # هر نیم ساعت چک کنه
    "15m": {"interval": 15, "unit": "min"},   # هر ۱۵ دقیقه
    "4h":  {"interval": 240, "unit": "min"},  # هر ۴ ساعت
    "1d":  {"interval": 1440, "unit": "min"}, # هر روز
}

# تعداد شمع‌های دریافتی برای هر تایم‌فریم
LIMIT = 500

# نام فایل‌های خروجی
CHART_FILE = BASE_DIR / "chart.html"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
ALL_DATA_FILE = DATA_DIR / "all_data.json"

# --- Bale Bot (نوتیفیکیشن) ---
BALE_TOKEN = "1210211811:m71ARq9K3c440dCYsBC1dtxfa5Bv630hMcI"
BALE_CHAT_ID = "506757503"
BALE_ENABLED = True  # برای غیرفعال کردن: False کنید


def csv_filename(symbol: str, timeframe: str) -> str:
    """ساخت نام فایل CSV از روی نماد و تایم‌فریم (در پوشه پروژه)"""
    pair = symbol.replace("/", "")
    return str(BASE_DIR / f"{pair}_{timeframe}.csv")