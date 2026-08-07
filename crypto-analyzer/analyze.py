# تحلیل: SMA + RSI + MACD + Bollinger Bands و سیگنال تقاطع
import pandas as pd

import notifier


def add_sma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """افزودن ستون میانگین متحرک ساده (SMA)"""
    df[f"sma_{window}"] = df["close"].rolling(window=window).mean()
    return df


def add_ema(df: pd.DataFrame, span: int = 12) -> pd.DataFrame:
    """افزودن میانگین متحرک نمایی (EMA)"""
    df[f"ema_{span}"] = df["close"].ewm(span=span, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """افزودن شاخص قدرت نسبی (RSI)"""
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """افزودن MACD (خط، سیگنال هیستوگرام)"""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["macd_signal"]
    return df


def add_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """افزودن باند بولینجر (بالا، پایین، میانگین)"""
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["bb_middle"] = sma
    df["bb_upper"] = sma + (std_dev * std)
    df["bb_lower"] = sma - (std_dev * std)
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """افزودن تمام اندیکاتورها به داده"""
    df = add_sma(df, window=9)
    df = add_sma(df, window=36)
    df = add_rsi(df, period=14)
    df = add_macd(df, fast=12, slow=26, signal=9)
    df = add_bollinger(df, period=20, std_dev=2.0)
    return df


def add_signals(df: pd.DataFrame, symbol: str = "", notify: bool = False) -> pd.DataFrame:
    """افزودن سیگنال خرید/فروش بر اساس تقاطع SMA9 و SMA36

    قوانین:
    - سیگنال فقط بعد از بسته شدن کندل صادر می‌شود (کندل i بسته شده است)
    - تقاطع صعودی: SMA9 از پایین به بالای SMA36 می‌رود و کلوز کندل بالای تقاطع است → خرید
    - تقاطع نزولی: SMA9 از بالا به پایین SMA36 می‌رود و کلوز کندل زیر تقاطع است → فروش
    - اگر notify=True باشد، سیگنال جدید به Bale ارسال می‌شود
    """
    df["signal"] = None
    last_signal_idx = None

    for i in range(1, len(df)):
        prev_9 = df["sma_9"].iloc[i - 1]
        prev_36 = df["sma_36"].iloc[i - 1]
        curr_9 = df["sma_9"].iloc[i]
        curr_36 = df["sma_36"].iloc[i]
        close = df["close"].iloc[i]

        if pd.isna(prev_9) or pd.isna(prev_36) or pd.isna(curr_9) or pd.isna(curr_36):
            continue

        # تقاطع صعودی: SMA9 از پایین به بالای SMA36 می‌رود
        if prev_9 <= prev_36 and curr_9 > curr_36:
            # کندل بسته شده باید بالای تقاطع باشد
            if close > curr_9 and close > curr_36:
                df.at[df.index[i], "signal"] = "buy"
                last_signal_idx = i

        # تقاطع نزولی: SMA9 از بالا به پایین SMA36 می‌رود
        elif prev_9 >= prev_36 and curr_9 < curr_36:
            # کندل بسته شده باید زیر تقاطع باشد
            if close < curr_9 and close < curr_36:
                df.at[df.index[i], "signal"] = "sell"
                last_signal_idx = i

    # ارسال نوتیف فقط برای آخرین سیگنال جدید
    if notify and last_signal_idx is not None and symbol:
        row = df.iloc[last_signal_idx]
        if pd.notna(row.get("signal")):
            rsi = row.get("rsi")
            macd_hist = row.get("macd_histogram")
            notifier.send_signal(
                symbol=symbol,
                signal_type=row["signal"],
                price=row["close"],
                timestamp=str(row["timestamp"]),
                rsi=float(rsi) if pd.notna(rsi) else None,
                macd_hist=float(macd_hist) if pd.notna(macd_hist) else None,
            )

    return df


def analyze_symbol(df: pd.DataFrame, symbol: str) -> None:
    """نمایش تحلیل پایه برای یک ارز"""
    print("\n" + "=" * 50)
    print(f"📊 تحلیل {symbol}")
    print("=" * 50)

    latest = df["close"].iloc[-1]
    first = df["close"].iloc[0]
    change = ((latest - first) / first) * 100

    print(f"آخرین قیمت: {latest:,.2f} USDT")
    print(f"اولین قیمت (دوره): {first:,.2f} USDT")
    print(f"تغییرات دوره: {change:+.2f}%")

    sma9 = df["sma_9"].iloc[-1]
    sma36 = df["sma_36"].iloc[-1]
    print(f"SMA9: {sma9:,.2f} USDT")
    print(f"SMA36: {sma36:,.2f} USDT")
    if sma9 > sma36:
        print("🟢 روند: صعودی (SMA9 بالای SMA36)")
    else:
        print("🔴 روند: نزولی (SMA9 پایین SMA36)")

    # --- RSI ---
    rsi = df["rsi"].iloc[-1]
    if not pd.isna(rsi):
        print(f"RSI (14): {rsi:.1f}", end="")
        if rsi > 70:
            print(" 🔴 اشباع خرید")
        elif rsi < 30:
            print(" 🟢 اشباع فروش")
        else:
            print(" ⚪ خنثی")

    # --- MACD ---
    macd_line = df["macd_line"].iloc[-1]
    macd_signal = df["macd_signal"].iloc[-1]
    macd_hist = df["macd_histogram"].iloc[-1]
    if not pd.isna(macd_line):
        print(f"MACD Line: {macd_line:,.2f}")
        print(f"MACD Signal: {macd_signal:,.2f}")
        print(f"MACD Histogram: {macd_hist:,.2f}", end="")
        if macd_hist > 0:
            print(" 🟢 صعودی")
        else:
            print(" 🔴 نزولی")

    # --- Bollinger Bands ---
    bb_upper = df["bb_upper"].iloc[-1]
    bb_middle = df["bb_middle"].iloc[-1]
    bb_lower = df["bb_lower"].iloc[-1]
    if not pd.isna(bb_upper):
        print(f"Bollinger Upper: {bb_upper:,.2f}")
        print(f"Bollinger Middle: {bb_middle:,.2f}")
        print(f"Bollinger Lower: {bb_lower:,.2f}")
        if latest > bb_upper:
            print("🔴 قیمت بالای باند بالا (اشباع خرید)")
        elif latest < bb_lower:
            print("🟢 قیمت زیر باند پایین (اشباع فروش)")
        else:
            print("⚪ قیمت در محدوده باند")

    signals = df[df["signal"].notna()]
    if not signals.empty:
        last_sig = signals.iloc[-1]
        sig_type = last_sig["signal"]
        sig_time = last_sig["timestamp"]
        if sig_type == "buy":
            print(f"🟢 آخرین سیگنال: خرید (تقاطع طلایی SMA9/SMA36) — {sig_time}")
        else:
            print(f"🔴 آخرین سیگنال: فروش (تقاطع مرگ SMA9/SMA36) — {sig_time}")
    else:
        print("⚪ هنوز سیگنالی ثبت نشده")

    last_volume = df["volume"].iloc[-1]
    avg_volume = df["volume"].tail(20).mean()
    print(f"حجم آخرین کندل: {last_volume:,.0f}")
    print(f"میانگین حجم (۲۰ کندل): {avg_volume:,.0f}")
    if last_volume > avg_volume * 1.5:
        print("📈 حجم بالاتر از میانگین — حرکت قوی")
    elif last_volume < avg_volume * 0.5:
        print("📉 حجم پایین‌تر از میانگین — حرکت ضعیف")
    else:
        print("⚪ حجم در حد میانگین")

    print(f"بالاترین قیمت دوره: {df['high'].max():,.2f} USDT")
    print(f"پایین‌ترین قیمت دوره: {df['low'].min():,.2f} USDT")


def analyze_all(data: dict) -> None:
    """تحلیل همه ارزها"""
    for symbol, df in data.items():
        analyze_symbol(df, symbol)
