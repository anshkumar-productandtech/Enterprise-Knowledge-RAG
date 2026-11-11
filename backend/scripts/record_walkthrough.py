"""Record a captioned screen walkthrough of the running app.

    python -m scripts.record_walkthrough --url http://localhost:3000 --out ../docs/walkthrough

Drives a real browser through the scenes in docs/walkthrough/scenes.json and
saves walkthrough.mp4. Nothing is staged: each closing caption is chosen from
what the assistant actually did (answered or declined), so the video cannot
claim a behaviour that did not happen on screen.

Needs: pip install playwright && python -m playwright install chromium, and ffmpeg.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCENES = BACKEND_DIR.parent / "docs" / "walkthrough" / "scenes.json"
SIZE = {"width": 1280, "height": 720}

CAPTION_JS = """
(text) => {
  let bar = document.getElementById('walkthrough-caption');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'walkthrough-caption';
    Object.assign(bar.style, {
      position: 'fixed', left: '50%', bottom: '28px', transform: 'translateX(-50%)',
      maxWidth: '860px', padding: '14px 22px', borderRadius: '10px', zIndex: '9999',
      background: 'rgba(23, 35, 58, 0.94)', color: '#fff', textAlign: 'center',
      font: '500 20px/1.4 "Public Sans Variable", system-ui, sans-serif',
      boxShadow: '0 6px 24px rgba(23, 35, 58, 0.25)', transition: 'opacity 200ms ease',
    });
    document.documentElement.appendChild(bar);
  }
  bar.style.opacity = text ? '1' : '0';
  if (text) bar.textContent = text;
}
"""


def caption(page: Page, text: str, hold: float) -> None:
    page.evaluate(CAPTION_JS, text)
    page.wait_for_timeout(int(hold * 1000))


def reading_time(text: str) -> float:
    """Long enough to read the caption at an unhurried pace."""
    return max(4.0, len(text.split()) / 2.6)


def play(page: Page, scenes: list[dict], answer_timeout_s: int) -> list[dict]:
    log: list[dict] = []
    for scene in scenes:
        if "ask" not in scene:
            caption(page, scene["caption"], scene.get("pause", reading_time(scene["caption"])))
            continue

        page.locator(".roles label", has_text=scene["role"]).first.click()
        caption(page, scene["caption"], reading_time(scene["caption"]))

        box = page.locator("#question")
        box.click()
        box.press_sequentially(scene["ask"], delay=28)
        page.wait_for_timeout(500)
        page.evaluate(CAPTION_JS, "")
        box.press("Enter")

        exchange = page.locator(".exchange").last
        exchange.locator(".receipt, .failure").first.wait_for(timeout=answer_timeout_s * 1000)
        exchange.scroll_into_view_if_needed()
        page.wait_for_timeout(1200)

        failed = exchange.locator(".failure").count() > 0
        refused = exchange.locator(".answer.is-refusal").count() > 0
        if failed:
            closing = "The request failed. See the message on screen."
        else:
            closing = scene["after_refused"] if refused else scene["after_answered"]

        cite = exchange.locator(".cite").first
        if scene.get("hover_cite") and not refused and not failed and cite.count():
            cite.hover()
        caption(page, closing, reading_time(closing) + 1.5)
        page.mouse.move(640, 80)
        log.append({"role": scene["role"], "question": scene["ask"], "refused": refused, "failed": failed})
    return log


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:3000")
    p.add_argument("--out", type=Path, default=DEFAULT_SCENES.parent)
    p.add_argument("--scenes", type=Path, default=DEFAULT_SCENES)
    p.add_argument("--answer-timeout", type=int, default=90)
    p.add_argument("--channel", default=None, help='e.g. "chrome" to use an installed browser')
    args = p.parse_args()

    scenes = json.loads(args.scenes.read_text(encoding="utf-8"))["scenes"]
    args.out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser = pw.chromium.launch(channel=args.channel, args=["--no-sandbox"])
        context = browser.new_context(viewport=SIZE, record_video_dir=tmp, record_video_size=SIZE)
        page = context.new_page()
        page.goto(args.url)
        page.locator(".starters button").first.wait_for(timeout=120_000)
        # The small-print disclosure sits where the captions go; the second caption states it instead.
        page.add_style_tag(content=".disclosure { visibility: hidden; }")
        page.wait_for_timeout(800)
        log = play(page, scenes, args.answer_timeout)
        context.close()  # finalises the recording
        browser.close()

        webm = next(Path(tmp).glob("*.webm"))
        mp4 = args.out / "walkthrough.mp4"
        if shutil.which("ffmpeg"):
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm), "-c:v", "libx264", "-preset", "slow",
                 "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(mp4)],
                check=True,
            )
        else:
            mp4 = args.out / "walkthrough.webm"
            shutil.copy(webm, mp4)

    (args.out / "walkthrough-log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Saved {mp4}")
    print(json.dumps(log, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
