# اجرای اصلی برنامه تحلیل کریپتو
import argparse
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

    # فقط آخرین سیگنال هر ارز در تایم‌فریم‌های تحت مانیتورینگ رو بفرست
    if notify:
        for timeframe in config.MONITOR_CONFIG:
            if timeframe not in analyzed:
                continue
            for symbol, df in analyzed[timeframe].items():
                signals = df[df["signal"].notna()]
                if signals.empty:
                    continue
                last_row = signals.iloc[-1]
                sig_time = last_row["timestamp"]
                now = datetime.now()
                cfg = config.MONITOR_CONFIG[timeframe]
                max_age_minutes = cfg["interval"] * 2
                if (now - sig_time).total_seconds() > max_age_minutes * 60:
                    continue
                rsi = last_row.get("rsi") if pd.notna(last_row.get("rsi")) else None
                macd_hist = last_row.get("macd_histogram") if pd.notna(last_row.get("macd_histogram")) else None
                bb_upper = last_row.get("bb_upper") if pd.notna(last_row.get("bb_upper")) else None
                bb_lower = last_row.get("bb_lower") if pd.notna(last_row.get("bb_lower")) else None
                sma9 = last_row.get("sma_9") if pd.notna(last_row.get("sma_9")) else None
                sma36 = last_row.get("sma_36") if pd.notna(last_row.get("sma_36")) else None
                notifier.send_signal(
                    symbol=symbol,
                    signal_type=last_row["signal"],
                    price=last_row["close"],
                    timestamp=str(sig_time),
                    rsi=rsi,
                    macd_hist=macd_hist,
                    bb_upper=bb_upper,
                    bb_lower=bb_lower,
                    sma9=sma9,
                    sma36=sma36,
                    chart_df=df,
                    timeframe=timeframe,
                )

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


def should_check_timeframe(timeframe: str, last_check: datetime | None) -> bool:
    """آیا الان وقت چک کردن این تایم‌فریم هست؟"""
    if last_check is None:
        return True
    cfg = config.MONITOR_CONFIG.get(timeframe)
    if not cfg:
        return False
    delta = timedelta(minutes=cfg["interval"])
    return datetime.now() - last_check >= delta


def run_monitor():
    """مانیتورینگ مداوم با فواصل زمانی مختلف"""
    print("=" * 60)
    print("حالت مانیتورینگ فعال شد")
    print(f"صرافی: {config.EXCHANGE_NAME}")
    print(f"ارزها: {', '.join(config.SYMBOLS)}")
    print(f"تایم‌فریم‌های تحت مانیتورینگ: {', '.join(config.MONITOR_CONFIG.keys())}")
    print("فواصل زمانی:")
    for tf, cfg in config.MONITOR_CONFIG.items():
        print(f"  {tf}: هر {cfg['interval']} دقیقه")
    print("=" * 60)
    print("برای خروج: Ctrl+C\n")

    last_check_times = {tf: None for tf in config.MONITOR_CONFIG}
    last_signals = {}

    while True:
        try:
            now = datetime.now()
            timeframes_to_check = [
                tf for tf in config.MONITOR_CONFIG
                if should_check_timeframe(tf, last_check_times[tf])
            ]

            if not timeframes_to_check:
                time.sleep(30)
                continue

            print(f"[{now.strftime('%H:%M:%S')}] چک تایم‌فریم‌ها: {', '.join(timeframes_to_check)}")

            data = fetch_data.fetch_all_timeframes(symbols=config.SYMBOLS, timeframes=timeframes_to_check)
            new_signal_found = False

            for timeframe, symbols in data.items():
                last_check_times[timeframe] = now
                for symbol, df in symbols.items():
                    df = analyze.add_all_indicators(df)
                    df = analyze.add_signals(df, symbol=symbol, notify=False)

                    signals = df[df["signal"].notna()]
                    if signals.empty:
                        continue

                    last_row = signals.iloc[-1]
                    key = f"{symbol}_{timeframe}"
                    signal_key = f"{last_row['signal']}_{last_row['timestamp']}"

                    if key not in last_signals or last_signals[key] != signal_key:
                        last_signals[key] = signal_key
                        new_signal_found = True
                        rsi = last_row.get("rsi") if pd.notna(last_row.get("rsi")) else None
                        macd_hist = last_row.get("macd_histogram") if pd.notna(last_row.get("macd_histogram")) else None
                        bb_upper = last_row.get("bb_upper") if pd.notna(last_row.get("bb_upper")) else None
                        bb_lower = last_row.get("bb_lower") if pd.notna(last_row.get("bb_lower")) else None
                        sma9 = last_row.get("sma_9") if pd.notna(last_row.get("sma_9")) else None
                        sma36 = last_row.get("sma_36") if pd.notna(last_row.get("sma_36")) else None

                        sig_emoji = "🟢" if last_row["signal"] == "buy" else "🔴"
                        sig_text = "خرید (BUY)" if last_row["signal"] == "buy" else "فروش (SELL)"
                        print(f"  {sig_emoji} {symbol} ({timeframe}): {sig_text}")

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
                        )

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
