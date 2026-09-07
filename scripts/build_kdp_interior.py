#!/usr/bin/env python3
"""
Build a KDP-paperback-ready interior PDF from a set of markdown chapter
files. Encodes the full working pipeline discovered and debugged across
real KDP rejections — see references/common-gotchas.md for why each piece
matters.

Usage:
    python3 build_kdp_interior.py --config book_config.json

book_config.json shape:
{
  "title": "The Turnaround Alibi",
  "subtitle": "How Leaders Manufacture Crisis, Capture Metrics, and Rewrite Success",
  "author": "Saravanakumar Karunanithi",
  "year": "2026",
  "isbn": "9798171424923",
  "publisher": "Independently Published via Kindle Direct Publishing",
  "dedication": "For everyone whose work became someone else's story.",
  "copyright_disclaimer": "This book is a work of nonfiction analysis...",
  "trim_width": 6,
  "trim_height": 9,
  "chapters": ["ch01.md", "ch02.md", ...],
  "frontmatter_chapters": ["acknowledgments.md", "prologue.md"],
  "backmatter_chapters": ["sources.md", "about_author.md"],
  "paper": "white"
}

Run this script TWICE through the whole pipeline if page count changes
materially — margin requirements and gutter safety math depend on final
page count, and the KDP cover spine width MUST be recalculated from the
final page count (use compute_cover_spec.py after this finishes).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
ASSETS = SKILL_DIR / "assets"

# Margin table: (max_pages, gutter_min, outer_min)
MARGIN_TABLE = [
    (150, 0.375, 0.25),
    (300, 0.5, 0.25),
    (500, 0.625, 0.25),
    (700, 0.75, 0.25),
    (828, 0.875, 0.25),
]

def minimum_margins(page_count):
    for max_pages, gutter, outer in MARGIN_TABLE:
        if page_count <= max_pages:
            return gutter, outer
    raise ValueError(f"Page count {page_count} exceeds KDP's 828-page paperback limit")

def safe_margins(page_count):
    """Minimum + safety buffer. Do not target the bare minimum -- see gotcha #3/#8."""
    gutter_min, outer_min = minimum_margins(page_count)
    return round(gutter_min + 0.25, 3), round(outer_min + 0.35, 3)

def build_body_markdown(chapters, appendix=None):
    parts = [Path(c).read_text() for c in chapters]
    if appendix:
        appendix_text = Path(appendix).read_text()
        appendix_text = re.sub(r'^# APPENDIX\n## (.+)$', r'# \1', appendix_text, flags=re.M)
        parts.append(appendix_text)
    body = "\n\n".join(p.rstrip("\n") for p in parts) + "\n"

    # Merge "# Chapter N\n## Title" into a single heading (LaTeX auto-numbers)
    body = re.sub(r'(?m)^# (Chapter \d+)\n## (.+)$', lambda m: f"# {m.group(2).strip()}", body)
    # Demote roman-numeral subsections one level
    body = re.sub(r'(?m)^### ', '## ', body)
    # Convert markdown "---" thematic breaks to an explicit, unambiguous raw-LaTeX
    # rule. Plain "---" sometimes leaks through as literal text -- see gotcha #4.
    rule_block = '```{=latex}\n\\begin{center}\\rule{0.4\\linewidth}{0.4pt}\\end{center}\n```'
    body = re.sub(r'(?m)^---[ \t]*$', lambda m: rule_block, body)

    # Warn about unspaced slashes -- see gotcha #5
    slash_words = re.findall(r'\b\w+/\w+\b', body)
    if slash_words:
        print(f"WARNING: {len(slash_words)} slash-joined word(s) found "
              f"(e.g. {slash_words[:3]}) -- these can break hyphenation and "
              f"cause overfull boxes. Consider adding spaces around slashes.",
              file=sys.stderr)

    return body

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workdir", default=".")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    workdir = Path(args.workdir)
    workdir.mkdir(exist_ok=True)

    # --- Step 0: ensure hyphenation is actually available (gotcha #1) ---
    check = subprocess.run(["kpsewhich", "hyph-en-us.tex"], capture_output=True, text=True)
    if not check.stdout.strip():
        print("English hyphenation patterns not found. Installing...", file=sys.stderr)
        subprocess.run(["apt-get", "install", "-y", "texlive-lang-english"], check=True)
        subprocess.run(["mktexlsr"], check=True)
        check2 = subprocess.run(["kpsewhich", "hyph-en-us.tex"], capture_output=True, text=True)
        if not check2.stdout.strip():
            print("ERROR: hyphenation patterns still not found after install + mktexlsr. "
                  "Stop and investigate before proceeding -- see gotcha #1.", file=sys.stderr)
            sys.exit(1)
        print("Hyphenation patterns installed and verified.", file=sys.stderr)

    # --- Step 1: build combined body markdown ---
    body_md = build_body_markdown(cfg["chapters"], cfg.get("appendix"))
    (workdir / "kdp_body.md").write_text(body_md)

    fm_md = "\n\n".join(Path(c).read_text().rstrip("\n") for c in cfg.get("frontmatter_chapters", []))
    fm_md = re.sub(r'(?m)^### ', '## ', fm_md)
    (workdir / "kdp_frontmatter.md").write_text(fm_md)

    bm_md = "\n\n".join(Path(c).read_text().rstrip("\n") for c in cfg.get("backmatter_chapters", []))
    bm_md = re.sub(r'(?m)^### ', '## ', bm_md)
    (workdir / "kdp_backmatter.md").write_text(bm_md)

    # --- Step 2: convert each to LaTeX fragments ---
    subprocess.run(["pandoc", str(workdir / "kdp_body.md"), "--to=latex",
                     "--top-level-division=chapter",
                     "-o", str(workdir / "kdp_body_frag.tex")], check=True)
    subprocess.run(["pandoc", str(workdir / "kdp_frontmatter.md"), "--to=latex",
                     "--top-level-division=chapter",
                     "-o", str(workdir / "kdp_frontmatter_frag.tex")], check=True)
    subprocess.run(["pandoc", str(workdir / "kdp_backmatter.md"), "--to=latex",
                     "--top-level-division=chapter",
                     "-o", str(workdir / "kdp_backmatter_frag.tex")], check=True)

    # Front/back matter chapters must be unnumbered (\chapter*, not \chapter)
    for frag_name in ["kdp_frontmatter_frag.tex", "kdp_backmatter_frag.tex"]:
        p = workdir / frag_name
        text = p.read_text()
        text = re.sub(r'\\chapter\{', r'\\chapter*{', text)
        p.write_text(text)

    # --- Step 3: build front-matter title/copyright/dedication pages ---
    fm_pages = (ASSETS / "front_matter_template.tex").read_text()
    fm_pages = fm_pages.replace("$TITLE_UPPER$", cfg["title"].upper())
    fm_pages = fm_pages.replace("$SUBTITLE$", cfg.get("subtitle", ""))
    fm_pages = fm_pages.replace("$AUTHOR$", cfg["author"])
    fm_pages = fm_pages.replace("$YEAR$", str(cfg["year"]))
    fm_pages = fm_pages.replace("$ISBN$", cfg.get("isbn", "[to be assigned]"))
    fm_pages = fm_pages.replace("$PUBLISHER$", cfg.get("publisher", "Independently Published via Kindle Direct Publishing"))
    fm_pages = fm_pages.replace("$DEDICATION$", cfg.get("dedication", ""))
    fm_pages = fm_pages.replace("$COPYRIGHT_DISCLAIMER$", cfg.get("copyright_disclaimer",
        "This book is a work of nonfiction. The views expressed are the author's own."))
    (workdir / "00a_front_matter_pages.tex").write_text(fm_pages)

    # --- Step 4: assemble the full document (2-pass: estimate page count, then finalize margins) ---
    # First pass: rough page count with default 213-ish assumption isn't reliable,
    # so compile once with conservative margins, read the actual count, then
    # recompile with correctly-sized safe margins if it changed materially.
    page_count_guess = cfg.get("estimated_pages", 250)
    gutter, outer = safe_margins(page_count_guess)

    template = (ASSETS / "kdp_template.tex").read_text()
    template = template.replace("$TRIM_WIDTH$", str(cfg.get("trim_width", 6)))
    template = template.replace("$TRIM_HEIGHT$", str(cfg.get("trim_height", 9)))
    template = template.replace("$GUTTER$", str(gutter))
    template = template.replace("$OUTER$", str(outer))
    template = template.replace("$TOPBOTTOM$", str(cfg.get("top_bottom_margin", 0.75)))

    body_frag = (workdir / "kdp_body_frag.tex").read_text()
    fm_frag = (workdir / "kdp_frontmatter_frag.tex").read_text()
    bm_frag = (workdir / "kdp_backmatter_frag.tex").read_text()

    final_tex = template.replace("$title$", cfg["title"]) \
                         .replace("$author$", cfg["author"]) \
                         .replace("$frontmatter$", fm_frag) \
                         .replace("$body$", body_frag) \
                         .replace("$backmatter$", bm_frag)
    (workdir / "kdp_final.tex").write_text(final_tex)

    # --- Step 5: compile (3 passes: TOC needs to converge) ---
    for i in range(3):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "kdp_final.tex"],
            cwd=workdir, capture_output=True, text=True
        )
        (workdir / f"kdp_run{i+1}.log").write_text(result.stdout + result.stderr)

    log = (workdir / "kdp_run3.log").read_text()
    if re.search(r'^!.*[Ee]rror|Fatal', log, re.M):
        print("ERROR: LaTeX compile errors found. Check kdp_run3.log before proceeding.", file=sys.stderr)
        sys.exit(1)

    overfull = re.findall(r'Overfull \\hbox \(([\d.]+)pt too wide\)', log)
    if overfull:
        worst = max(float(x) for x in overfull)
        worst_in = worst / 72
        remaining = gutter - worst_in
        print(f"{len(overfull)} overfull box(es), worst = {worst:.2f}pt ({worst_in:.3f}in)", file=sys.stderr)
        print(f"Remaining gutter after worst-case overflow: {remaining:.3f}in "
              f"(need >= {minimum_margins(page_count_guess)[0]}in)", file=sys.stderr)
        if remaining < minimum_margins(page_count_guess)[0]:
            print("WARNING: worst-case overflow may breach KDP's minimum gutter. "
                  "Check emergencystretch is in the template (it should be, by default). "
                  "See references/common-gotchas.md items 1-5.", file=sys.stderr)

    pdf_path = workdir / "kdp_final.pdf"
    print(f"Built: {pdf_path}", file=sys.stderr)
    print("Next: run compute_cover_spec.py with the FINAL page count from this PDF, "
          "then build the cover. If this is a re-run after content edits, the cover "
          "must be rebuilt too -- see gotcha #6.", file=sys.stderr)

if __name__ == "__main__":
    main()
