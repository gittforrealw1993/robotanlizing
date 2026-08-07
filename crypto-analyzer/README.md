# 🪙 Crypto Analyzer Bot

ربات تحلیل تکنیکال کریپتو با ارسال سیگنال خرید/فروش به بله.

## 📌 ویژگی‌ها

- تحلیل تکنیکال بر اساس **تقاطع SMA9/SMA36**
- پشتیبانی از **SMA, RSI, MACD, Bollinger Bands**
- ارسال خودکار سیگنال به **ربات بله** با عکس چارت
- حالت مانیتورینگ مداوم برای **سرور**
- پشتیبانی از **BTC, ETH, WLD, NEAR, DOGE**
- چارت تعاملی TradingView

---

## 🚀 نصب و راه‌اندازی

### ۱. کلون پروژه

```bash
git clone https://github.com/YOUR_USERNAME/crypto-analyzer.git
cd crypto-analyzer
```

### ۲. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### ۳. تنظیم متغیرها

```bash
cp .env.example .env
```

فایل `.env` رو ویرایش کن:

```env
BALE_TOKEN=your_bale_bot_token_here
BALE_CHAT_ID=your_chat_id_here
BALE_ENABLED=true
```

### ۴. اجرا

```bash
# اجرای یکبار (با باز شدن چارت در مرورگر)
python main.py

# اجرای یکبار (بدون چارت)
python main.py --mode once --no-chart

# اجرای مداوم (برای سرور)
python main.py --mode monitor
```

---

## 🐳 اجرا با Docker

```bash
docker-compose up -d
```

---

## 📊 سیگنال‌ها

### منطق سیگنال خرید (Golden Cross):
```
SMA9 از پایین به بالای SMA36 قطع کند
AND کلوز کندل بالای هر دو SMA باشد
```

### منطق سیگنال فروش (Death Cross):
```
SMA9 از بالا به پایین SMA36 قطع کند
AND کلوز کندل زیر هر دو SMA باشد
```

---

## ⏰ زمان‌بندی مانیتورینگ

| تایم‌فریم | هر چند دقیقه چک میشه |
|-----------|---------------------|
| 15m | 15 دقیقه |
| 1h | 30 دقیقه |
| 4h | 4 ساعت |
| 1d | 24 ساعت |

---

## 📁 ساختار پروژه

```
crypto-analyzer/
├── main.py              # نقطه ورود + لوپ مانیتورینگ
├── config.py            # تنظیمات مرکزی
├── fetch_data.py        # دریافت داده از صرافی
├── analyze.py           # تحلیل تکنیکال + سیگنال
├── generate_chart.py    # چارت HTML TradingView
├── notifier.py          # ارسال سیگنال به بله
├── chart_screenshot.py  # اسکرین‌شات چارت
├── requirements.txt     # وابستگی‌ها
├── Dockerfile           # داکر
├── docker-compose.yml   # داکر کامپوز
├── .env.example         # نمونه متغیرها
└── .gitignore
```

---

## ⚙️ تنظیمات سرور (VPS)

```bash
# اجرای پایدار با nohup
nohup python main.py --mode monitor > analyzer.log 2>&1 &

# یا با systemd
sudo cp crypto-analyzer.service /etc/systemd/system/
sudo systemctl enable crypto-analyzer
sudo systemctl start crypto-analyzer
```

---

## 📝 لایسنس

MIT
