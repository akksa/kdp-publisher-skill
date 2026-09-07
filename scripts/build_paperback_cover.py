#!/usr/bin/env python3
"""
Build a print-ready, KDP-compliant wraparound paperback cover PDF.

Uses a clean typographic design (no stock photography, no licensing risk) --
this is the right default for nonfiction/business books and sidesteps image
licensing entirely. For fiction or genres that need illustration, adapt the
front-cover drawing section but keep the panel-boundary math untouched.

Usage:
    python3 build_paperback_cover.py --config book_config.json --pages 217 --out cover.pdf

Re-run this any time the interior page count changes (gotcha #6).
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def spine_width(page_count, paper="white"):
    per_page = 0.002252 if paper == "white" else 0.0025
    return page_count * per_page

def build_cover(cfg, page_count, out_path, dpi=300):
    IN = lambda x: round(x * dpi)
    bleed = IN(0.125)
    trim_w = IN(cfg.get("trim_width", 6))
    trim_h = IN(cfg.get("trim_height", 9))
    spine = IN(spine_width(page_count, cfg.get("paper", "white")))

    cover_w = bleed + trim_w + spine + trim_w + bleed
    cover_h = bleed + trim_h + bleed

    back_end = bleed + trim_w
    spine_start = back_end
    spine_end = spine_start + spine
    front_start = spine_end

    BG = tuple(cfg.get("bg_color", [17, 18, 20]))
    WHITE = tuple(cfg.get("title_color", [245, 245, 243]))
    GRAY = tuple(cfg.get("kicker_color", [168, 170, 175]))
    LIGHT_GRAY = tuple(cfg.get("body_color", [200, 202, 206]))
    ACCENT = tuple(cfg.get("accent_color", [196, 68, 44]))
    RULE_GRAY = (70, 72, 76)

    img = Image.new("RGB", (cover_w, cover_h), BG)
    draw = ImageDraw.Draw(img)

    font_dir = cfg.get("font_dir", "/usr/share/fonts/truetype/dejavu/")
    def font(name, size):
        return ImageFont.truetype(font_dir + name, size)
    def text_wh(txt, fnt):
        bbox = draw.textbbox((0, 0), txt, font=fnt)
        return bbox[2]-bbox[0], bbox[3]-bbox[1]
    def draw_centered(cx, y, txt, fnt, fill):
        w, h = text_wh(txt, fnt)
        draw.text((cx - w/2, y), txt, font=fnt, fill=fill)
        return h

    # ---- FRONT COVER ----
    fc_left = front_start + IN(0.25)
    fc_right = cover_w - bleed - IN(0.25)
    fc_center = (front_start + cover_w) // 2

    if cfg.get("kicker"):
        kicker_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.155))
        draw_centered(fc_center, IN(1.55), cfg["kicker"], kicker_font, GRAY)
        draw.rectangle([fc_center - IN(0.55), IN(1.92), fc_center + IN(0.55), IN(1.95)], fill=ACCENT)

    title_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.70))
    y = IN(2.25)
    for line in cfg["title_lines"]:
        draw_centered(fc_center, y, line, title_font, WHITE)
        y += IN(0.72)

    y_rule = y + IN(0.02)
    draw.rectangle([fc_left + IN(0.2), y_rule, fc_right - IN(0.2), y_rule + IN(0.04)], fill=ACCENT)

    if cfg.get("subtitle_lines"):
        sub_font = font("DejaVuSerif.ttf", IN(0.185))
        y2 = y_rule + IN(0.22)
        for line in cfg["subtitle_lines"]:
            draw_centered(fc_center, y2, line, sub_font, LIGHT_GRAY)
            y2 += IN(0.28)

    author_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.20))
    draw.rectangle([fc_center - IN(0.85), cover_h - bleed - IN(0.70), fc_center + IN(0.85), cover_h - bleed - IN(0.68)], fill=RULE_GRAY)
    draw_centered(fc_center, cover_h - bleed - IN(0.52), cfg["author"].upper(), author_font, WHITE)

    # ---- SPINE ----
    spine_cx = (spine_start + spine_end) // 2
    if spine >= IN(0.0625) * 2:  # only draw spine text if there's room; skip below 79pg equiv width
        spine_title_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.20))
        tw, th = text_wh(cfg["title"], spine_title_font)
        txt_img = Image.new("RGBA", (tw+20, th+30), (0,0,0,0))
        ImageDraw.Draw(txt_img).text((10,0), cfg["title"], font=spine_title_font, fill=WHITE)
        rotated_title = txt_img.rotate(90, expand=True)

        spine_author_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.145))
        last_name = cfg["author"].split()[-1].upper()
        aw, ah = text_wh(last_name, spine_author_font)
        a_img = Image.new("RGBA", (aw+20, ah+30), (0,0,0,0))
        ImageDraw.Draw(a_img).text((10,0), last_name, font=spine_author_font, fill=GRAY)
        rotated_author = a_img.rotate(90, expand=True)

        gap = IN(0.35)
        total_h = rotated_title.height + gap + rotated_author.height
        start_y = cover_h//2 - total_h//2
        img.paste(rotated_title, (spine_cx - rotated_title.width//2, start_y), rotated_title)
        img.paste(rotated_author, (spine_cx - rotated_author.width//2, start_y + rotated_title.height + gap), rotated_author)

    # ---- BACK COVER ----
    bc_left = bleed + IN(0.25)
    if cfg.get("back_cover_hook"):
        hook_font = font("DejaVuSansCondensed-Bold.ttf", IN(0.15))
        hy = IN(0.75)
        for line in cfg["back_cover_hook"]:
            draw.text((bc_left, hy), line, font=hook_font, fill=ACCENT)
            hy += IN(0.24)

    if cfg.get("back_cover_blurb"):
        blurb_font = font("DejaVuSerif.ttf", IN(0.135))
        blurb_bold = font("DejaVuSerif-Bold.ttf", IN(0.135))
        y = IN(1.45)
        for line in cfg["back_cover_blurb"]:
            fnt = blurb_bold if line.get("bold") else blurb_font
            draw.text((bc_left, y), line["text"], font=fnt, fill=WHITE if line.get("bold") else LIGHT_GRAY)
            y += IN(0.205)

    # Bottom-right of back cover left deliberately blank for KDP's auto barcode --
    # do NOT draw a border or placeholder there (gotcha: it should render, not just
    # be reserved space that happens to be empty by accident).

    img.save(out_path, "PDF", resolution=dpi)
    return cover_w, cover_h, spine

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--out", default="cover.pdf")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    w, h, spine = build_cover(cfg, args.pages, args.out)
    print(f"Cover built: {args.out}")
    print(f"Size: {w/300:.4f}in x {h/300:.4f}in  (spine: {spine/300:.4f}in)")

if __name__ == "__main__":
    main()
