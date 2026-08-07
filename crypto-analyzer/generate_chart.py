# تولید فایل HTML با چارت تعاملی TradingView Lightweight Charts — طراحی ساده
import json
import webbrowser

import pandas as pd

import config


def _columns_to_json(df: pd.DataFrame, col_name: str) -> list:
    """تبدیل یک ستون اندیکاتور به لیست {time, value}"""
    pts = []
    for _, row in df.iterrows():
        t = int(row["timestamp"].timestamp())
        val = row.get(col_name)
        if val is not None and not pd.isna(val):
            pts.append({"time": t, "value": float(val)})
    return pts


def _build_json(analyzed: dict) -> str:
    """تبدیل همه داده‌های تحلیل‌شده به JSON برای جاسازی در HTML"""
    json_data = {}
    for timeframe, symbols in analyzed.items():
        json_data[timeframe] = {}
        for symbol, df in symbols.items():
            candles = []
            volume = []
            for _, row in df.iterrows():
                t = int(row["timestamp"].timestamp())
                candles.append({
                    "time": t,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
                volume.append({"time": t, "value": float(row["volume"])})

            ind = {
                "sma_9": _columns_to_json(df, "sma_9"),
                "sma_36": _columns_to_json(df, "sma_36"),
                "bb_upper": _columns_to_json(df, "bb_upper"),
                "bb_middle": _columns_to_json(df, "bb_middle"),
                "bb_lower": _columns_to_json(df, "bb_lower"),
                "rsi": _columns_to_json(df, "rsi"),
                "macd_line": _columns_to_json(df, "macd_line"),
                "macd_signal": _columns_to_json(df, "macd_signal"),
                "macd_histogram": _columns_to_json(df, "macd_histogram"),
            }

            signals = []
            for _, row in df.iterrows():
                sig = row.get("signal")
                if sig is not None and not pd.isna(sig):
                    signals.append({
                        "time": int(row["timestamp"].timestamp()),
                        "type": str(sig),
                        "price": float(row["close"]),
                    })

            json_data[timeframe][symbol] = {
                "candles": candles,
                "volume": volume,
                "ind": ind,
                "signals": signals,
            }

    return json.dumps(json_data)


def build_chart_html(analyzed: dict, chart_file: str = str(config.CHART_FILE)) -> str:
    """ساخت فایل HTML با چارت قیمت + SMA9/SMA36 + سیگنال + حجم (طراحی ساده)"""
    data_json = _build_json(analyzed)
    symbols_json = json.dumps(list(config.SYMBOLS))

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تحلیل کریپتو</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Vazirmatn', 'B Nazanin', Tahoma, Arial, sans-serif;
            min-height: 100vh;
            background: #F8FAFC;
            color: #1E293B;
            padding: 24px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            padding: 16px 24px;
            margin-bottom: 24px;
            background: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        }}
        h1 {{
            font-size: 20px;
            font-weight: 600;
            color: #0F172A;
        }}
        .header-controls {{ display: flex; align-items: center; gap: 12px; }}
        .header-controls label {{ color: #64748B; font-size: 13px; }}
        select {{
            background: #F8FAFC;
            color: #0F172A;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 14px;
            cursor: pointer;
            font-family: inherit;
            outline: none;
        }}
        select:hover {{ border-color: #4F46E5; }}
        select option {{ background: #fff; color: #0F172A; }}

        /* کارت‌ها — زیر هم */
        .chart-box {{
            background: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .chart-box h2 {{
            font-size: 18px;
            font-weight: 600;
            color: #0F172A;
        }}
        .controls {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
        .btn.rsi-btn.active {{ color: #F59E0B; border-color: #F59E0B; background: rgba(245, 158, 11, 0.06); }}
        .btn.macd-btn.active {{ color: #EC4899; border-color: #EC4899; background: rgba(236, 72, 153, 0.06); }}
        .btn.bb-btn.active {{ color: #8B5CF6; border-color: #8B5CF6; background: rgba(139, 92, 246, 0.06); }}
        .indicator-panel {{
            margin-top: 12px;
            border-top: 1px solid rgba(0,0,0,0.05);
            padding-top: 12px;
            display: none;
        }}
        .indicator-panel.visible {{ display: block; }}
        .panel-label {{
            font-size: 11px;
            color: #64748B;
            margin-bottom: 6px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .btn {{
            background: #F8FAFC;
            color: #64748B;
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 10px;
            padding: 6px 14px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }}
        .btn:hover {{ color: #0F172A; }}
        .btn.active {{
            color: #4F46E5;
            border-color: #4F46E5;
            background: rgba(79, 70, 229, 0.06);
        }}

        .price-chart {{ position: relative; border-radius: 12px; overflow: hidden; }}
        .tooltip {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 12px;
            pointer-events: none;
            z-index: 10;
            display: none;
            line-height: 1.8;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            color: #0F172A;
        }}
        .green {{ color: #10B981; }}
        .red {{ color: #EF4444; }}
        .yellow {{ color: #F59E0B; }}
    </style>
</head>
<body>
<div class="container">
<header>
    <h1>📊 تحلیل کریپتو</h1>
    <div class="header-controls">
        <label>تایم‌فریم</label>
        <select id="tf-select">
            {''.join(f'<option value="{tf}"{" selected" if tf == config.TIMEFRAME else ""}>{tf}</option>' for tf in config.TIMEFRAMES)}
        </select>
    </div>
</header>
<div id="charts"></div>
</div>

<script>
const ALL_DATA = {data_json};
const SYMBOLS = {symbols_json};
const PREFERRED_TF = new URLSearchParams(window.location.search).get('tf') || '{config.TIMEFRAME}';

document.getElementById('tf-select').value = PREFERRED_TF;
document.getElementById('tf-select').addEventListener('change', e => {{
    window.location.search = '?tf=' + e.target.value;
}});

function fmtNum(n) {{
    return n.toLocaleString('fa-IR');
}}

function fmtTime(ts) {{
    const d = new Date(ts * 1000);
    return d.toLocaleString('fa-IR', {{
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit',
    }});
}}

function createChart(container, height) {{
    return LightweightCharts.createChart(container, {{
        width: container.clientWidth || 900,
        height: height,
        layout: {{
            backgroundColor: 'transparent',
            textColor: '#64748B',
            fontFamily: 'Vazirmatn, Tahoma, sans-serif',
        }},
        grid: {{
            vertLines: {{ color: 'rgba(15,23,42,0.03)' }},
            horzLines: {{ color: 'rgba(15,23,42,0.03)' }},
        }},
        rightPriceScale: {{ borderColor: 'rgba(15,23,42,0.05)' }},
        timeScale: {{
            borderColor: 'rgba(15,23,42,0.05)',
            rightOffset: 5,
            barSpacing: 7,
            timeVisible: true,
            secondsVisible: false,
        }},
        crosshair: {{
            vertLine: {{ color: 'rgba(79,70,229,0.3)', width: 1, style: 3 }},
            horzLine: {{ color: 'rgba(79,70,229,0.3)', width: 1, style: 3 }},
        }},
    }});
}}

function buildSymbolChart(symbol, data, container) {{
     const box = document.createElement('div');
     box.className = 'chart-box';
     box.innerHTML = `<div class="chart-header">
             <h2>${{symbol}}</h2>
         </div>
         <div class="controls">
             <button class="btn active" data-ind="sma_9">SMA 9</button>
             <button class="btn active" data-ind="sma_36">SMA 36</button>
             <button class="btn bb-btn" data-ind="bb">Bollinger</button>
             <button class="btn rsi-btn" data-ind="rsi">RSI</button>
             <button class="btn macd-btn" data-ind="macd">MACD</button>
             <button class="btn" data-ind="volume">حجم</button>
         </div>
         <div class="price-chart"></div>
         <div class="indicator-panel" id="rsi-panel">
             <div class="panel-label">RSI (14) — اشباع خرید > 70 | اشباع فروش < 30</div>
             <div class="rsi-chart"></div>
         </div>
         <div class="indicator-panel" id="macd-panel">
             <div class="panel-label">MACD (12, 26, 9)</div>
             <div class="macd-chart"></div>
         </div>`;
     container.appendChild(box);

     const chart = createChart(box.querySelector('.price-chart'), 400);

     // --- چارت اصلی قیمت ---
     const candleSeries = chart.addCandlestickSeries({{
         upColor: '#10B981', downColor: '#EF4444', borderVisible: false,
         wickUpColor: '#10B981', wickDownColor: '#EF4444',
     }});
     candleSeries.setData(data.candles);

     // حجم (histogram) — پیش‌فرض غیرفعال
     const volumeSeries = chart.addHistogramSeries({{
         priceScaleId: 'vol',
         priceFormat: {{ type: 'volume' }},
         scaleMargins: {{ top: 0.82, bottom: 0 }},
         visible: false,
     }});
     volumeSeries.setData(data.volume.map(v => ({{
         time: v.time, value: v.value,
         color: 'rgba(16, 185, 129, 0.2)',
     }})));

     // --- خطوط SMA ---
     const smaSeries = {{
         sma_9: chart.addLineSeries({{
             color: '#4F46E5', lineWidth: 2, title: 'SMA9',
             priceLineVisible: false, lastValueVisible: true,
         }}),
         sma_36: chart.addLineSeries({{
             color: '#7C3AED', lineWidth: 2, title: 'SMA36',
             priceLineVisible: false, lastValueVisible: true,
         }}),
     }};
     Object.keys(smaSeries).forEach(key => {{
         smaSeries[key].setData(data.ind[key] || []);
     }});

     // --- باند بولینجر ---
     const bbSeries = {{
         bb_upper: chart.addLineSeries({{
             color: '#8B5CF6', lineWidth: 1, title: 'BB Upper',
             priceLineVisible: false, lastValueVisible: false,
         }}),
         bb_middle: chart.addLineSeries({{
             color: '#A78BFA', lineWidth: 1, lineStyle: 2, title: 'BB Mid',
             priceLineVisible: false, lastValueVisible: false,
         }}),
         bb_lower: chart.addLineSeries({{
             color: '#8B5CF6', lineWidth: 1, title: 'BB Lower',
             priceLineVisible: false, lastValueVisible: false,
         }}),
     }};
     Object.keys(bbSeries).forEach(key => {{
         bbSeries[key].setData(data.ind[key] || []);
         bbSeries[key].applyOptions({{ visible: false }});
     }});

     // --- RSI Panel ---
     const rsiPanel = box.querySelector('#rsi-panel');
     const rsiChart = createChart(box.querySelector('.rsi-chart'), 120);
     const rsiSeries = rsiChart.addLineSeries({{
         color: '#F59E0B', lineWidth: 2, title: 'RSI',
         priceLineVisible: false, lastValueVisible: true,
     }});
     rsiSeries.setData(data.ind.rsi || []);
     // RSI reference lines at 30 and 70
     rsiSeries.createPriceLine({{ price: 70, color: '#EF4444', lineWidth: 1, lineStyle: 3, axisLabelVisible: true, title: 'اشباع خرید' }});
     rsiSeries.createPriceLine({{ price: 30, color: '#10B981', lineWidth: 1, lineStyle: 3, axisLabelVisible: true, title: 'اشباع فروش' }});
     rsiSeries.createPriceLine({{ price: 50, color: '#94A3B8', lineWidth: 1, lineStyle: 2, axisLabelVisible: false }});

     // --- MACD Panel ---
     const macdPanel = box.querySelector('#macd-panel');
     const macdChart = createChart(box.querySelector('.macd-chart'), 120);
     const macdLineSeries = macdChart.addLineSeries({{
         color: '#EC4899', lineWidth: 2, title: 'MACD',
         priceLineVisible: false, lastValueVisible: true,
     }});
     macdLineSeries.setData(data.ind.macd_line || []);
     const macdSignalSeries = macdChart.addLineSeries({{
         color: '#3B82F6', lineWidth: 1, title: 'Signal',
         priceLineVisible: false, lastValueVisible: false,
     }});
     macdSignalSeries.setData(data.ind.macd_signal || []);
     const macdHistSeries = macdChart.addHistogramSeries({{
         priceScaleId: 'macd-hist',
         priceFormat: {{ type: 'price' }},
     }});
     macdHistSeries.setData((data.ind.macd_histogram || []).map(v => ({{
         time: v.time, value: v.value,
         color: v.value >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)',
     }})));

     // مارکرهای سیگنال خرید/فروش
     const markers = data.signals.map(s => {{
         const isBuy = s.type === 'buy';
         return {{
             time: s.time,
             position: isBuy ? 'belowBar' : 'aboveBar',
             color: isBuy ? '#10B981' : '#EF4444',
             shape: isBuy ? 'arrowUp' : 'arrowDown',
             text: isBuy ? 'خرید' : 'فروش',
         }};
     }});
     if (markers.length) candleSeries.setMarkers(markers);

     // --- دکمه‌های فعال/غیرفعال ---
     box.querySelectorAll('.btn').forEach(btn => {{
         btn.addEventListener('click', () => {{
             const active = btn.classList.toggle('active');
             const ind = btn.dataset.ind;
             if (ind === 'volume') {{
                 volumeSeries.applyOptions({{ visible: active }});
             }} else if (ind === 'bb') {{
                 Object.keys(bbSeries).forEach(k => bbSeries[k].applyOptions({{ visible: active }}));
             }} else if (ind === 'rsi') {{
                 rsiPanel.classList.toggle('visible', active);
                 setTimeout(() => rsiChart.timeScale().fitContent(), 50);
             }} else if (ind === 'macd') {{
                 macdPanel.classList.toggle('visible', active);
                 setTimeout(() => macdChart.timeScale().fitContent(), 50);
             }} else {{
                 smaSeries[ind].applyOptions({{ visible: active }});
             }}
         }});
     }});

     // --- تولتیپ ---
     const tooltip = document.createElement('div');
     tooltip.className = 'tooltip';
     box.querySelector('.price-chart').appendChild(tooltip);
     chart.subscribeCrosshairMove(param => {{
         if (!param.time) {{ tooltip.style.display = 'none'; return; }}
         tooltip.style.display = 'block';
         let price = '';
         if (param.seriesData && param.seriesData.get(candleSeries)) {{
             const c = param.seriesData.get(candleSeries);
             price = `قیمت: {{fmtNum(c.close)}}`;
         }}
         tooltip.innerHTML = `⏱ کلوز: {{fmtTime(param.time)}}<br>{{price}}`;
     }});

     chart.timeScale().fitContent();
 }}

// ساخت چارت برای هر ارز
const chartsContainer = document.getElementById('charts');
SYMBOLS.forEach(sym => {{
    const data = ALL_DATA[PREFERRED_TF][sym];
    buildSymbolChart(sym, data, chartsContainer);
}});

// به‌روزرسانی اندازه چارت‌ها هنگام تغییر سایز
window.addEventListener('resize', () => {{
    document.querySelectorAll('.price-chart').forEach(el => {{
        LightweightCharts.charts().forEach(c => c.applyOptions({{ width: el.clientWidth }}));
    }});
}});
</script>
</body>
</html>"""

    with open(chart_file, "w", encoding="utf-8") as f:
        f.write(html)

    return chart_file


def open_chart(chart_file: str = str(config.CHART_FILE)) -> None:
    """باز کردن چارت در مرورگر"""
    webbrowser.open(chart_file)