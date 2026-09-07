#!/usr/bin/env python3
"""
Render specific pages of a built interior PDF to PNG for visual inspection.

Always run this on:
  - The half-title, title, copyright, dedication, and TOC pages after any
    front-matter change (checking right/left-facing rules held).
  - Any page KDP's reviewer flags by number, after every fix attempt --
    never assume a fix worked without re-rendering the exact flagged page.
  - At least one even-numbered page deep in the body, to sanity-check
    gutter margin visually.

Usage:
    python3 verify_pages.py --pdf kdp_final.pdf --pages 1,2,3,4,52,62 --dpi 150
"""
import argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--pages", required=True, help="comma-separated page numbers")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("pip install pdf2image --break-system-packages", flush=True)
        raise

    pages = [int(p.strip()) for p in args.pages.split(",")]
    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    for p in pages:
        imgs = convert_from_path(args.pdf, first_page=p, last_page=p, dpi=args.dpi)
        out_path = outdir / f"verify_page_{p}.png"
        imgs[0].save(out_path)
        print(f"Rendered page {p} -> {out_path}")

if __name__ == "__main__":
    main()
