# تنظیمات پروژه تحلیل کریپتو
import os
from pathlib import Path

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent

# --- بارگذاری .env ---
def _load_env():
    """خواندن فایل .env بدون کتابخانه خارجی"""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

_load_env()

# --- صرافی ---
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "toobit")

# --- لیست ارزها ---
SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "WLD/USDT",
    "NEAR/USDT",
    "DOGE/USDT",
]

# --- تایم‌فریم‌ها ---
TIMEFRAMES = ["5m", "15m", "30m", "1h", "4h", "1d"]
TIMEFRAME = "1h"

# --- تنظیمات داده ---
LIMIT = int(os.getenv("LIMIT", "500"))

# --- فایل‌های خروجی ---
CHART_FILE = BASE_DIR / "chart.html"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
ALL_DATA_FILE = DATA_DIR / "all_data.json"

# --- Bale Bot ---
BALE_TOKEN = os.getenv("BALE_TOKEN", "")
BALE_CHAT_ID = os.getenv("BALE_CHAT_ID", "")
BALE_ENABLED = os.getenv("BALE_ENABLED", "true").lower() == "true"

# --- مانیتورینگ ---
MONITOR_CONFIG = {
    "30m": {"interval": int(os.getenv("MONITOR_30M_INTERVAL", "30")), "unit": "min"},
    "1h":  {"interval": int(os.getenv("MONITOR_1H_INTERVAL", "60")), "unit": "min"},
}

# --- مدیریت ریسک سیگنال ---
SWING_LOOKBACK = int(os.getenv("SWING_LOOKBACK", "20"))
REWARD_RISK_MULT = float(os.getenv("REWARD_RISK_MULT", "2.0"))


def csv_filename(symbol: str, timeframe: str) -> str:
    """ساخت نام فایل CSV"""
    pair = symbol.replace("/", "")
    return str(BASE_DIR / f"{pair}_{timeframe}.csv")
