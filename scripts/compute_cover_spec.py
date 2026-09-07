#!/usr/bin/env python3
"""
Compute exact KDP paperback cover dimensions from a page count.

MUST be re-run any time the interior's page count changes, even by a few
pages -- the spine width is a direct function of page count, and a cover
sized for the wrong page count is one of the most common late-stage KDP
rejection causes (see references/common-gotchas.md, gotcha #6).

Usage:
    python3 compute_cover_spec.py --pages 217 --trim-width 6 --trim-height 9 --paper white
"""
import argparse

def spine_width(page_count, paper="white"):
    per_page = 0.002252 if paper == "white" else 0.0025
    return page_count * per_page

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--trim-width", type=float, default=6)
    ap.add_argument("--trim-height", type=float, default=9)
    ap.add_argument("--paper", choices=["white", "cream"], default="white")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    bleed = 0.125
    spine_in = spine_width(args.pages, args.paper)
    cover_w = bleed + args.trim_width + spine_in + args.trim_width + bleed
    cover_h = bleed + args.trim_height + bleed

    back_end = bleed + args.trim_width
    spine_start = back_end
    spine_end = spine_start + spine_in
    front_start = spine_end

    dpi = args.dpi
    print(f"Page count: {args.pages}  Paper: {args.paper}")
    print(f"Spine width: {spine_in:.4f} in")
    print(f"Full cover: {cover_w:.4f} in x {cover_h:.4f} in")
    print(f"At {dpi} DPI: {round(cover_w*dpi)} x {round(cover_h*dpi)} px")
    print()
    print("Panel boundaries (inches from left edge):")
    print(f"  Back cover:  0.000 to {back_end:.4f}")
    print(f"  Spine:       {spine_start:.4f} to {spine_end:.4f}")
    print(f"  Front cover: {front_start:.4f} to {cover_w:.4f}")
    print()
    print("Panel boundaries (pixels at {} DPI):".format(dpi))
    print(f"  Back cover:  0 to {round(back_end*dpi)}")
    print(f"  Spine:       {round(spine_start*dpi)} to {round(spine_end*dpi)}")
    print(f"  Front cover: {round(front_start*dpi)} to {round(cover_w*dpi)}")
    print()
    if spine_in * 72 < 4.5:  # roughly under ~0.0625in text clearance both sides won't fit spine text nicely below ~79pg equivalent
        print("NOTE: spine is narrow. KDP requires >=79 pages for spine text to be")
        print("eligible at all, and text needs >=0.0625in clearance from each spine edge.")

if __name__ == "__main__":
    main()
