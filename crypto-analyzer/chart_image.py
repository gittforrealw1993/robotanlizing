# تولید عکس چارت برای پیوست شدن به سیگنال
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from matplotlib.patches import Rectangle

import config


def generate_chart_image(df: pd.DataFrame, symbol: str, timeframe: str,
                         signal_type: str = None) -> bytes | None:
    """تولید عکس چارت کندل‌استیک با اندیکاتورها

    Args:
        df: DataFrame با ستون‌های timestamp, open, high, low, close, volume + اندیکاتورها
        symbol: نام ارز
        timeframe: تایم‌فریم
        signal_type: نوع سیگنال (buy/sell) برای نمایش روی چارت

    Returns:
        بایت‌های عکس PNG یا None
    """
    try:
        df = df.dropna(subset=["sma_9", "sma_36"]).reset_index(drop=True)
        if len(df) < 2:
            return None

        df = df.tail(80)

        fig, axes = plt.subplots(3, 1, figsize=(12, 8), height_ratios=[3, 1, 1], facecolor="#1a1a2e")
        ax1, ax2, ax3 = axes
        ax1.set_facecolor("#16213e")
        ax2.set_facecolor("#16213e")
        ax3.set_facecolor("#16213e")

        dates = df["timestamp"]

        for i, row in df.iterrows():
            x = mdates.date2num(row["timestamp"])
            color = "#10B981" if row["close"] >= row["open"] else "#EF4444"

            ax1.plot([x, x], [row["low"], row["high"]], color=color, linewidth=0.8)
            body_low = min(row["open"], row["close"])
            body_high = max(row["open"], row["close"])
            body_height = body_high - body_low
            if body_height == 0:
                body_height = 0.01
            rect = Rectangle((x - 0.3, body_low), 0.6, body_height,
                             facecolor=color, edgecolor=color, linewidth=0.5)
            ax1.add_patch(rect)

            if signal_type and pd.notna(row.get("signal")):
                if row["signal"] == "buy":
                    ax1.scatter(x, row["low"] * 0.998, marker="^", color="#10B981",
                                s=120, zorder=5, edgecolors="white", linewidths=0.5)
                elif row["signal"] == "sell":
                    ax1.scatter(x, row["high"] * 1.002, marker="v", color="#EF4444",
                                s=120, zorder=5, edgecolors="white", linewidths=0.5)

        if "sma_9" in df.columns:
            ax1.plot(dates, df["sma_9"], color="#818cf8", linewidth=1.2, label="SMA 9", alpha=0.9)
        if "sma_36" in df.columns:
            ax1.plot(dates, df["sma_36"], color="#a78bfa", linewidth=1.2, label="SMA 36", alpha=0.9)
        if "bb_upper" in df.columns:
            ax1.plot(dates, df["bb_upper"], color="#c084fc", linewidth=0.8, linestyle="--",
                     alpha=0.6, label="BB Upper")
            ax1.plot(dates, df["bb_lower"], color="#c084fc", linewidth=0.8, linestyle="--",
                     alpha=0.6, label="BB Lower")
            ax1.fill_between(dates, df["bb_lower"], df["bb_upper"], alpha=0.05, color="#c084fc")

        ax1.legend(loc="upper left", fontsize=8, facecolor="#16213e", edgecolor="#334155",
                   labelcolor="white")
        ax1.set_title(f"{symbol} | {timeframe}", color="white", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Price (USDT)", color="#94a3b8", fontsize=10)
        ax1.tick_params(colors="#94a3b8", labelsize=8)
        ax1.grid(True, alpha=0.1, color="#475569")
        for spine in ax1.spines.values():
            spine.set_color("#334155")

        colors = ["#10B981" if row["close"] >= row["open"] else "#EF4444"
                  for _, row in df.iterrows()]
        ax2.bar(dates, df["volume"], color=colors, alpha=0.6, width=0.6)
        ax2.set_ylabel("Volume", color="#94a3b8", fontsize=10)
        ax2.tick_params(colors="#94a3b8", labelsize=8)
        ax2.grid(True, alpha=0.1, color="#475569")
        for spine in ax2.spines.values():
            spine.set_color("#334155")

        if "rsi" in df.columns:
            ax3.plot(dates, df["rsi"], color="#fbbf24", linewidth=1.2, label="RSI (14)")
            ax3.axhline(y=70, color="#ef4444", linestyle="--", alpha=0.5, linewidth=0.8)
            ax3.axhline(y=30, color="#10b981", linestyle="--", alpha=0.5, linewidth=0.8)
            ax3.fill_between(dates, 30, 70, alpha=0.05, color="#fbbf24")
            ax3.legend(loc="upper left", fontsize=8, facecolor="#16213e", edgecolor="#334155",
                       labelcolor="white")
        ax3.set_ylabel("RSI", color="#94a3b8", fontsize=10)
        ax3.set_ylim(0, 100)
        ax3.tick_params(colors="#94a3b8", labelsize=8)
        ax3.grid(True, alpha=0.1, color="#475569")
        for spine in ax3.spines.values():
            spine.set_color("#334155")

        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right")
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=30, ha="right")

        last_price = df["close"].iloc[-1]
        price_color = "#10B981" if df["close"].iloc[-1] >= df["close"].iloc[-2] else "#EF4444"
        ax1.text(0.99, 0.97, f"${last_price:,.2f}", transform=ax1.transAxes,
                 fontsize=12, fontweight="bold", color=price_color,
                 ha="right", va="top",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e293b", edgecolor="#475569"))

        sig_emoji = "BUY" if signal_type == "buy" else "SELL"
        sig_color = "#10B981" if signal_type == "buy" else "#EF4444"
        ax1.text(0.01, 0.97, sig_emoji, transform=ax1.transAxes,
                 fontsize=11, fontweight="bold", color=sig_color,
                 ha="left", va="top",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="#1e293b", edgecolor=sig_color))

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    except Exception as e:
        print(f"  خطا در تولید عکس چارت: {e}")
        return None
