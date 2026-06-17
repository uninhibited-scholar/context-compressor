"""Generate the GitHub social-preview card (1280x640 PNG).

    python assets/make_social_preview.py

Upload the result at: repo → Settings → Social preview → Upload an image.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640
BG = (13, 17, 23)        # GitHub dark
FG = (230, 237, 243)
MUTED = (139, 148, 158)
ACCENT = (46, 160, 67)   # green
HERE = os.path.dirname(__file__)


def _font(size: int, bold: bool = False):
    candidates = (
        ["/System/Library/Fonts/SFNSDisplay-Bold.otf",
         "/Library/Fonts/Arial Bold.ttf",
         "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
        if bold else
        ["/System/Library/Fonts/SFNS.ttf",
         "/Library/Fonts/Arial.ttf",
         "/System/Library/Fonts/Supplemental/Arial.ttf"]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # accent bar
    d.rectangle([0, 0, 14, H], fill=ACCENT)

    pad = 70
    d.text((pad, 70), "Context Compressor", font=_font(74, bold=True), fill=FG)
    d.text((pad, 168),
           "Shrink LLM context windows by 40–80%",
           font=_font(40, bold=True), fill=ACCENT)
    d.text((pad, 232),
           "Remove noise, redundancy & long-tail detail — without losing signal.",
           font=_font(30), fill=MUTED)

    bullets = [
        "Zero dependencies · pure Python",
        "Noise · dedup · trim · extractive summary",
        "LangChain / LlamaIndex adapters",
        "Security-scan brief generator",
        "tiktoken-accurate token metrics + CLI",
    ]
    y = 320
    for b in bullets:
        d.ellipse([pad, y + 12, pad + 14, y + 26], fill=ACCENT)
        d.text((pad + 34, y), b, font=_font(30), fill=FG)
        y += 52

    d.text((pad, H - 66),
           "pip install llm-context-compressor",
           font=_font(32, bold=True), fill=FG)
    d.text((W - 430, H - 66), "MIT · github.com/uninhibited-scholar",
           font=_font(24), fill=MUTED)

    out = os.path.join(HERE, "social-preview.png")
    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
