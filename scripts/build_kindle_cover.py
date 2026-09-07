#!/usr/bin/env python3
"""
Build a Kindle eBook cover -- single front-only image, NOT a wraparound.
Different spec entirely from the paperback cover (see
references/kdp-formatting-spec.md, Kindle eBook section).

Native 1.6:1 ratio at 2000x3200px (2x the 1000x1600 minimum-quality
recommendation, for crispness). Do not just crop/stretch the paperback
front panel -- its ratio (~1.5:1 for a 6x9 trim) doesn't match Kindle's
1.6:1 closely enough to reuse cleanly. Rebuild natively.

Usage:
    python3 build_kindle_cover.py --config book_config.json --out kindle_cover.jpg
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="kindle_cover.jpg")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())

    W, H = 2000, 3200  # exact 1.6:1, 2x recommended minimum resolution

    BG = tuple(cfg.get("bg_color", [17, 18, 20]))
    WHITE = tuple(cfg.get("title_color", [245, 245, 243]))
    GRAY = tuple(cfg.get("kicker_color", [168, 170, 175]))
    LIGHT_GRAY = tuple(cfg.get("body_color", [200, 202, 206]))
    ACCENT = tuple(cfg.get("accent_color", [196, 68, 44]))
    RULE_GRAY = (70, 72, 76)

    img = Image.new("RGB", (W, H), BG)  # RGB, never CMYK -- Kindle spec
    draw = ImageDraw.Draw(img)

    font_dir = cfg.get("font_dir", "/usr/share/fonts/truetype/dejavu/")
    def font(name, size):
        return ImageFont.truetype(font_dir + name, size)
    def text_w(txt, fnt):
        bbox = draw.textbbox((0, 0), txt, font=fnt)
        return bbox[2]-bbox[0], bbox[3]-bbox[1]
    def draw_centered(cx, y, txt, fnt, fill):
        w, h = text_w(txt, fnt)
        draw.text((cx - w/2, y), txt, font=fnt, fill=fill)
        return h

    cx = W // 2
    left_margin = int(W * 0.10)
    right_margin = W - left_margin

    if cfg.get("kicker"):
        kicker_font = font("DejaVuSansCondensed-Bold.ttf", 52)
        draw_centered(cx, 480, cfg["kicker"], kicker_font, GRAY)
        draw.rectangle([cx - 190, 590, cx + 190, 598], fill=ACCENT)

    title_font = font("DejaVuSansCondensed-Bold.ttf", 230)
    y = 700
    for line in cfg["title_lines"]:
        draw_centered(cx, y, line, title_font, WHITE)
        y += 235

    y_rule = y + 10
    draw.rectangle([left_margin + 60, y_rule, right_margin - 60, y_rule + 14], fill=ACCENT)

    if cfg.get("subtitle_lines"):
        sub_font = font("DejaVuSerif.ttf", 62)
        y2 = y_rule + 70
        for line in cfg["subtitle_lines"]:
            draw_centered(cx, y2, line, sub_font, LIGHT_GRAY)
            y2 += 92

    author_font = font("DejaVuSansCondensed-Bold.ttf", 68)
    draw.rectangle([cx - 280, H - 340, cx + 280, H - 334], fill=RULE_GRAY)
    draw_centered(cx, H - 270, cfg["author"].upper(), author_font, WHITE)

    img.save(args.out, "JPEG", quality=95, dpi=(300, 300))
    print(f"Kindle cover built: {args.out}  ({W}x{H}, ratio {H/W:.2f}:1, RGB)")

if __name__ == "__main__":
    main()
