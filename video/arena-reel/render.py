"""Render index.html frame by frame with Chromium and encode the Reel.

Usage:
  python render.py stills 0 5 10.5 ...   # PNG previews into out/stills/
  python render.py video                 # full 50 s render -> out/arena-reel.mp4
"""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "out"
FPS, DURATION = 30, 50
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
# Pre-installed Chromium (the pip playwright version may expect a different browser build)
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def open_page(p):
    browser = p.chromium.launch(executable_path=CHROMIUM if Path(CHROMIUM).exists() else None)
    page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    page.goto((ROOT / "index.html").as_uri())
    caps = json.loads((ROOT / "captions.json").read_text(encoding="utf-8"))
    page.evaluate("caps => window.init(caps)", caps)
    return browser, page


def stills(times):
    (OUT / "stills").mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_page(p)
        for t in times:
            page.evaluate(f"window.render({t})")
            page.screenshot(path=str(OUT / "stills" / f"t{t:05.2f}.png"))
        browser.close()


def video():
    OUT.mkdir(exist_ok=True)
    silent = OUT / "video-silent.mp4"
    enc = subprocess.Popen(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), str(silent)],
        stdin=subprocess.PIPE,
    )
    with sync_playwright() as p:
        browser, page = open_page(p)
        for f in range(FPS * DURATION):
            page.evaluate(f"window.render({f / FPS})")
            enc.stdin.write(page.screenshot(type="png"))
            if f % 150 == 0:
                print(f"frame {f}/{FPS * DURATION}", flush=True)
        browser.close()
    enc.stdin.close()
    enc.wait()

    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(OUT / "audio.wav"),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
         str(OUT / "arena-reel.mp4")],
        check=True,
    )
    silent.unlink()
    # cover / thumbnail taken from the CTA scene
    with sync_playwright() as p:
        browser, page = open_page(p)
        page.evaluate("window.render(48.4)")
        page.screenshot(path=str(OUT / "cover.png"))
        browser.close()


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills([float(x) for x in sys.argv[2:]])
    else:
        video()
