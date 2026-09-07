#!/usr/bin/env python3
"""
Build a Kindle-ready reflowable DOCX from the same markdown chapter set
used for the paperback. Different file entirely from the paperback PDF --
see references/kdp-formatting-spec.md, Kindle eBook section, for why.

Usage:
    python3 build_kindle_ebook.py --config book_config.json --out kindle.docx

Kindle's own converter builds device navigation automatically from Word
"Heading 1" styles (which is what pandoc's "# Heading" produces) -- no
manual Table of Contents field is used or needed here, deliberately: a
Word TOC field is fragile through KDP's conversion pipeline in practice.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="kindle_ebook.docx")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())

    front_matter = f"""**{cfg['title']}**

*{cfg.get('subtitle', '')}*

{cfg['author']}

Copyright © {cfg['year']} by {cfg['author']}

All rights reserved.

{cfg.get('copyright_disclaimer', '')}

Published by {cfg.get('publisher', 'Independently Published via Kindle Direct Publishing')}.

*{cfg.get('dedication', '')}*
"""

    chapter_files = cfg["chapters"]
    chapter_titles = cfg["chapter_titles"]  # list of plain titles, same order as chapter_files

    body_parts = [Path(c).read_text() for c in chapter_files]
    if cfg.get("appendix"):
        appendix_text = Path(cfg["appendix"]).read_text()
        appendix_text = re.sub(r'^# APPENDIX\n## (.+)$', r'# \1', appendix_text, flags=re.M)
        body_parts.append(appendix_text)

    fm_extra = [Path(c).read_text() for c in cfg.get("frontmatter_chapters", [])]
    back_parts = [Path(c).read_text() for c in cfg.get("backmatter_chapters", [])]

    all_parts = [front_matter] + fm_extra + body_parts + back_parts
    text = "\n\n".join(p.rstrip("\n") for p in all_parts) + "\n"

    text = re.sub(r'(?m)^# (Chapter \d+)\n## (.+)$', lambda m: f"# {m.group(2).strip()}", text)
    text = re.sub(r'(?m)^### ', '## ', text)
    text = re.sub(r'(?m)^---\s*$', '', text)  # no thick-bar dividers in docx output

    # Add chapter numbers back (Word doesn't auto-number the way LaTeX \chapter does)
    for i, title in enumerate(chapter_titles, 1):
        old = f"# {title}"
        new = f"# Chapter {i}: {title}"
        assert text.count(old) == 1, f"expected exactly one match for {title!r}, got {text.count(old)}"
        text = text.replace(old, new)

    # Page break before every top-level heading except the very first (front matter)
    pagebreak = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'
    lines = text.split('\n')
    out, seen_first = [], False
    for line in lines:
        if line.startswith('# '):
            if seen_first:
                out.append(pagebreak.rstrip('\n'))
                out.append('')
            seen_first = True
        out.append(line)
    text = '\n'.join(out)

    md_path = Path(args.out).with_suffix('.md')
    md_path.write_text(text)

    subprocess.run(["pandoc", str(md_path), "-o", args.out], check=True)
    print(f"Kindle eBook built: {args.out}")
    print("Upload this DOCX in the Kindle eBook format step in KDP (separate from "
          "the paperback format step). No ISBN needed for this format.")

if __name__ == "__main__":
    main()
