# نوتیفیکیشن به ربات Bale برای سیگنال‌های خرید/فروش
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests

import config


def send_to_bale(text: str) -> dict | None:
    """ارسال متن به ربات Bale"""
    url = f"https://tapi.bale.ai/bot{config.BALE_TOKEN}/sendMessage"
    payload = {"chat_id": config.BALE_CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  |-- Bale status: {response.status_code}")
            return None
    except Exception as e:
        print(f"  |-- Bale error: {e}")
        return None


def send_photo_to_bale(photo_bytes: bytes, caption: str = "") -> dict | None:
    """ارسال عکس به ربات Bale"""
    url = f"https://tapi.bale.ai/bot{config.BALE_TOKEN}/sendPhoto"
    files = {"photo": ("chart.png", photo_bytes, "image/png")}
    data = {"chat_id": config.BALE_CHAT_ID, "caption": caption}
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  |-- Bale Photo status: {response.status_code}")
            return None
    except Exception as e:
        print(f"  |-- Bale Photo error: {e}")
        return None


def send_signal(symbol: str, signal_type: str, price: float, timestamp: str,
                rsi: float = None, macd_hist: float = None,
                bb_upper: float = None, bb_lower: float = None,
                sma9: float = None, sma36: float = None,
                chart_df=None, timeframe: str = "") -> dict:
    """ساخت و ارسال پیام سیگنال + اسکرین‌شات چارت"""
    if not config.BALE_ENABLED:
        return None

    is_buy = signal_type == "buy"
    sig_emoji = "🟢" if is_buy else "🔴"
    sig_type_fa = "خرید" if is_buy else "فروش"
    sig_type_en = "BUY" if is_buy else "SELL"
    cross_type = "تقاطع طلایی Golden Cross" if is_buy else "تقاطع مرگ Death Cross"
    trend = "صعودی" if is_buy else "نزولی"

    rsi_val = f"{rsi:.1f}" if rsi is not None else "N/A"
    macd_val = f"{macd_hist:,.2f}" if macd_hist is not None else "N/A"
    bb_up_val = f"{bb_upper:,.2f}" if bb_upper is not None else "N/A"
    bb_low_val = f"{bb_lower:,.2f}" if bb_lower is not None else "N/A"

    text = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sig_emoji} سیگنال {sig_type_fa} | {sig_type_en}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🪙 ارز: {symbol}
💰 قیمت: ${price:,.2f} USDT
⏰ زمان: {timestamp}
📐 تایم‌فریم: {timeframe}
📈 روند: {trend}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 استراتژی: تقاطع SMA9 / SMA36
⚡ نوع سیگنال: {cross_type}

📋 اندیکاتورها:
  • SMA9: {sma9:,.2f} | SMA36: {sma36:,.2f}
  • RSI(14): {rsi_val}
  • MACD Hist: {macd_val}
  • BB Upper: {bb_up_val} | BB Lower: {bb_low_val}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Crypto Analyzer Bot
📡 صرافی: {config.EXCHANGE_NAME}
━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    try:
        if timeframe:
            print("  |-- در حال گرفتن اسکرین‌شات...")
            import chart_screenshot
            screenshot_bytes = chart_screenshot.take_chart_screenshot(symbol, timeframe)
            if screenshot_bytes:
                send_photo_to_bale(screenshot_bytes, caption=f"{symbol} | {timeframe}")
                print("  |-- عکس ارسال شد")

        result = send_to_bale(text)
        if result is not None:
            print("  |-- سیگنال ارسال شد")
            return result
        else:
            print("  |-- سیگنال ارسال نشد")
            return None
    except Exception as e:
        print(f"  |-- خطا: {e}")
        return None
