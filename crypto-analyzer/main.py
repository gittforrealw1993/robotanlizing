# اجرای اصلی برنامه تحلیل کریپتو
import argparse
import json
import sys
import time
from datetime import datetime, timedelta

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

import analyze
import config
import fetch_data
import generate_chart
import notifier

LAST_SIGNALS_FILE = config.DATA_DIR / "last_signals.json"


def load_last_signals() -> dict:
    """بارگذاری وضعیت آخرین سیگنال‌ها از فایل (dedup پایدار)"""
    try:
        if LAST_SIGNALS_FILE.exists():
            with open(LAST_SIGNALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_last_signals(state: dict) -> None:
    """ذخیره وضعیت آخرین سیگنال‌ها در فایل"""
    try:
        with open(LAST_SIGNALS_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  |-- خطا در ذخیره dedup: {e}")


def _signal_key(row) -> str:
    """کلید یکتا برای یک سیگنال (نوع + زمان)"""
    return f"{row['signal']}_{row['timestamp']}"


def is_recent(row, timeframe: str, cfg) -> bool:
    """آیا سیگنال به‌اندازه کافی تازه است که بفرستیم؟"""
    sig_time = row["timestamp"]
    if isinstance(sig_time, str):
        sig_time = pd.Timestamp(sig_time)
    max_age = timedelta(minutes=cfg["interval"] * 2)
    return datetime.now() - sig_time <= max_age


def maybe_send_signal(symbol, timeframe, df, last_signals):
    """اگر سیگنال آخرِ df تازه و جدید بود، بفرست و در dedup ثبت کن"""
    signals = df[df["signal"].notna()]
    if signals.empty:
        return False
    last_row = signals.iloc[-1]
    key = f"{symbol}_{timeframe}"
    sig_key = _signal_key(last_row)

    # dedup: اگر همین سیگنال قبلاً فرستاده شده، رد شو
    if last_signals.get(key) == sig_key:
        return False

    # فیلتر سن: سیگنال کهنه مثل BTC 1d یک‌ماهه فرستاده نشود
    cfg = config.MONITOR_CONFIG.get(timeframe)
    if cfg is None or not is_recent(last_row, timeframe, cfg):
        return False

    rsi = last_row.get("rsi") if pd.notna(last_row.get("rsi")) else None
    macd_hist = last_row.get("macd_histogram") if pd.notna(last_row.get("macd_histogram")) else None
    bb_upper = last_row.get("bb_upper") if pd.notna(last_row.get("bb_upper")) else None
    bb_lower = last_row.get("bb_lower") if pd.notna(last_row.get("bb_lower")) else None
    sma9 = last_row.get("sma_9") if pd.notna(last_row.get("sma_9")) else None
    sma36 = last_row.get("sma_36") if pd.notna(last_row.get("sma_36")) else None
    entry = last_row.get("entry") if pd.notna(last_row.get("entry")) else None
    stop_loss = last_row.get("stop_loss") if pd.notna(last_row.get("stop_loss")) else None
    tp1 = last_row.get("tp1") if pd.notna(last_row.get("tp1")) else None
    tp2 = last_row.get("tp2") if pd.notna(last_row.get("tp2")) else None
    tp3 = last_row.get("tp3") if pd.notna(last_row.get("tp3")) else None

    sig_emoji = "🟢" if last_row["signal"] == "buy" else "🔴"
    sig_text = "خرید (BUY)" if last_row["signal"] == "buy" else "فروش (SELL)"
    print(f"  {sig_emoji} {symbol} ({timeframe}): {sig_text} @ {last_row['timestamp']}")

    notifier.send_signal(
        symbol=symbol,
        signal_type=last_row["signal"],
        price=last_row["close"],
        timestamp=str(last_row["timestamp"]),
        rsi=rsi,
        macd_hist=macd_hist,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        sma9=sma9,
        sma36=sma36,
        chart_df=df,
        timeframe=timeframe,
        entry=entry,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
    )

    last_signals[key] = sig_key
    return True


def run_once(notify: bool = True, open_chart: bool = True):
    """اجرای یکبار تحلیل — فقط آخرین سیگنال هر ارز/تایم‌فریم"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] شروع تحلیل...")
    print(f"صرافی: {config.EXCHANGE_NAME}")

    all_data = fetch_data.fetch_all_timeframes()

    analyzed = {}
    for timeframe, symbols in all_data.items():
        analyzed[timeframe] = {}
        for symbol, df in symbols.items():
            filename = config.csv_filename(symbol, timeframe)
            df.to_csv(filename, index=False)
            df = analyze.add_all_indicators(df)
            df = analyze.add_signals(df, symbol=symbol, notify=False)
            analyzed[timeframe][symbol] = df

    # فقط سیگنال تازه + جدید (dedup پایدار) هر ارز در تایم‌فریم‌های تحت مانیتورینگ رو بفرست
    if notify:
        last_signals = load_last_signals()
        for timeframe in config.MONITOR_CONFIG:
            if timeframe not in analyzed:
                continue
            for symbol, df in analyzed[timeframe].items():
                maybe_send_signal(symbol, timeframe, df, last_signals)
        save_last_signals(last_signals)

    print("\n" + "=" * 60)
    print(f"تحلیل تایم‌فریم پیش‌فرض: {config.TIMEFRAME}")
    print("=" * 60)
    analyze.analyze_all(analyzed[config.TIMEFRAME])

    print("\nدر حال ساخت چارت TradingView ...")
    chart_file = generate_chart.build_chart_html(analyzed)
    print(f"چارت ساخته شد: {chart_file}")

    if open_chart:
        generate_chart.open_chart(chart_file)

    return analyzed


def aligned_check_minutes(timeframe: str) -> list:
    """دقایقِ ساعت که چک باید انجام شود (همگام با باز شدن کندل)"""
    if timeframe == "30m":
        return [1, 31]   # بعد از بسته‌شدن کندل 30 دقیقه‌ای (0:00 و 0:30)
    if timeframe == "1h":
        return [1]       # بعد از بسته‌شدن کندل ساعتی (ساعت رند)
    return []


def next_check_time(timeframe: str, now: datetime | None = None) -> datetime:
    """زمان رند بعدی برای چک یک تایم‌فریم (مثل 12:01 و 12:31)"""
    now = now or datetime.now()
    minutes = aligned_check_minutes(timeframe)
    if not minutes:
        return now
    today = now.replace(second=0, microsecond=0)
    for minute in sorted(minutes):
        candidate = today.replace(minute=minute)
        if candidate > now:
            return candidate
    # فردا — اولین دقیقه
    return (today.replace(minute=minutes[0]) + timedelta(days=1))


def run_monitor():
    """مانیتورینگ مداوم با چک همگام با ساعت (زمان رند)"""
    print("=" * 60)
    print("حالت مانیتورینگ فعال شد")
    print(f"صرافی: {config.EXCHANGE_NAME}")
    print(f"ارزها: {', '.join(config.SYMBOLS)}")
    print(f"تایم‌فریم‌های تحت مانیتورینگ: {', '.join(config.MONITOR_CONFIG.keys())}")
    for tf in config.MONITOR_CONFIG:
        print(f"  {tf}: چک در دقایق {aligned_check_minutes(tf)} هر ساعت")
    print("=" * 60)
    print("برای خروج: Ctrl+C\n")

    next_checks = {tf: next_check_time(tf) for tf in config.MONITOR_CONFIG}
    last_signals = load_last_signals()

    while True:
        try:
            now = datetime.now()
            timeframes_to_check = [
                tf for tf in config.MONITOR_CONFIG
                if now >= next_checks[tf]
            ]

            if not timeframes_to_check:
                time.sleep(20)
                continue

            for tf in timeframes_to_check:
                next_checks[tf] = next_check_time(tf, now)

            print(f"[{now.strftime('%H:%M:%S')}] چک تایم‌فریم‌ها: {', '.join(timeframes_to_check)}")

            data = fetch_data.fetch_all_timeframes(symbols=config.SYMBOLS, timeframes=timeframes_to_check)
            new_signal_found = False

            for timeframe, symbols in data.items():
                for symbol, df in symbols.items():
                    df = analyze.add_all_indicators(df)
                    df = analyze.add_signals(df, symbol=symbol, notify=False)
                    if maybe_send_signal(symbol, timeframe, df, last_signals):
                        new_signal_found = True

            save_last_signals(last_signals)

            if not new_signal_found:
                print(f"  ⚪ سیگنال جدیدی نیست")

            time.sleep(30)

        except KeyboardInterrupt:
            print("\nخروج از مانیتورینگ...")
            break
        except Exception as e:
            print(f"خطا: {e}")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="تحلیل کریپتو")
    parser.add_argument(
        "--mode",
        choices=["once", "monitor"],
        default="once",
        help="once = اجرای تکی | monitor = مانیتورینgh مداوم برای سرور",
    )
    parser.add_argument(
        "--no-chart",
        action="store_true",
        help="چارت در مرورگر باز نشود",
    )

    args = parser.parse_args()

    if args.mode == "monitor":
        run_monitor()
    else:
        run_once(notify=True, open_chart=not args.no_chart)


if __name__ == "__main__":
    main()
