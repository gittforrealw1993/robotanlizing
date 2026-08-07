# اسکرین‌شات از چارت HTML با html2image (Edge)
import sys
import os
import tempfile

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import config


def take_chart_screenshot(symbol: str, timeframe: str = None) -> bytes | None:
    """اسکرین‌شات از چارت HTML"""
    if timeframe is None:
        timeframe = config.TIMEFRAME

    chart_path = config.CHART_FILE
    if not chart_path.exists():
        print("  |-- چارت HTML پیدا نشد")
        return None

    try:
        from html2image import Html2Image
        tmp_dir = tempfile.mkdtemp()
        tmp_png = os.path.join(tmp_dir, "shot.png")

        hti = Html2Image(output_path=tmp_dir, browser="edge", size=(1400, 900))
        url = f"file:///{chart_path.absolute().as_posix()}?tf={timeframe}"
        hti.screenshot(url=url, save_as="shot.png")

        if os.path.exists(tmp_png):
            with open(tmp_png, "rb") as f:
                png_bytes = f.read()
            os.unlink(tmp_png)
            os.rmdir(tmp_dir)
            return png_bytes
        return None
    except Exception as e:
        print(f"  |-- خطا در اسکرین‌شات: {e}")
        return None
