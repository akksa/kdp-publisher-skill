---
name: kdp-book-publisher
description: Converts manuscript content (markdown chapters, an uploaded PDF, or a Word doc) into a complete, KDP-upload-ready publishing package — a print-ready paperback interior PDF, a matching wraparound cover PDF, a reflowable Kindle eBook file, a Kindle-specific front-only cover, and draft listing metadata (description, categories, keywords). Use this whenever the user wants to self-publish a book on Amazon KDP, asks to "format for KDP," "make this publishable," "prepare a paperback/Kindle edition," "build a book cover" for Amazon, or asks why a KDP upload was rejected for margin/gutter/cover-size errors. Also use it if the user pastes a KDP quality-check error message (insufficient gutter, cover size mismatch, text outside margins) even without saying "KDP" explicitly — these are recognizable, specific error strings this skill knows how to diagnose and fix.
---

# KDP Book Publisher

Turns manuscript content into an actual KDP-ready publishing package, using
a pipeline debugged against real KDP rejections rather than KDP's spec
alone. **The spec is necessary but not sufficient** — several of the real
failure modes below only surface after actual submission, and chasing them
without the fixes in `references/common-gotchas.md` costs many debugging
cycles. Read that file before touching margins or fonts if anything looks
like a margin/gutter/overflow problem.

## What this produces

1. **Paperback interior** — print-ready PDF, correct KDP front/back matter
   order, twoside mirrored margins, proper hyphenation, chapter starts on
   right-facing pages.
2. **Paperback cover** — full wraparound PDF (back + spine + front), spine
   width computed from actual page count.
3. **Kindle eBook interior** — reflowable DOCX, different file entirely
   from the paperback (see gotchas — do not try to reuse the PDF).
4. **Kindle cover** — single front-only JPEG, different ratio and spec from
   the paperback cover.
5. **Listing metadata** — draft description, categories, keywords.

## Workflow

### 0. Ingest the source content

If given a PDF or DOCX instead of markdown chapters, extract the text first
(use the `pdf` / `docx` skills' reading guidance if available) and split it
into one markdown file per chapter, preserving heading structure (`#` for
chapter title, `##`/`###` for sections). This skill's scripts expect a list
of chapter markdown files, not a single combined document — building the
combined document is what `build_kdp_interior.py` does.

Ask the user (or infer from context) for: title, subtitle, author name,
year, whether they already have an ISBN or want the free KDP one, and
whether they want paperback only, Kindle only, or both. Don't block on
every field — reasonable placeholders (e.g. `ISBN: [to be assigned]`) are
fine to start with and easy to swap in later once they have the real value.

### 1. Build `book_config.json`

See the full example schema in `scripts/build_kdp_interior.py`'s docstring.
Minimum required: `title`, `author`, `year`, `chapters` (ordered list of
markdown file paths). Everything else has a sensible default.

### 2. Build the paperback interior

```bash
python3 scripts/build_kdp_interior.py --config book_config.json --workdir build/
```

This script already encodes the hard-won fixes: it verifies hyphenation
patterns are actually installed (not just claimed installed — see gotcha
#1), applies `emergencystretch`/`tolerance` so overflow gets absorbed by
spacing instead of breaking margins (gotcha #2), and computes a *safe*
margin (minimum + buffer) rather than the bare KDP minimum.

**Check the script's stderr output for overfull-box warnings and the
computed remaining-gutter number.** If it warns that remaining gutter may
be insufficient, do not just re-run with wider margins — re-read gotcha #3
first (widening margins can make wrapping worse, not better) and look for
the *specific* cause using the isolation technique in gotcha #5 before
touching margin numbers again.

### 3. Verify visually — always, every time

```bash
python3 scripts/verify_pages.py --pdf build/kdp_final.pdf --pages 1,2,3,4,5,6,7,8
```

Check: half-title on page 1 (right-facing), blank page 2, title page 3
(right-facing), copyright page 4, dedication page 5 (right-facing), TOC
starting page 6/7 (right-facing, no header/page number). Then render a few
body pages, including at least one even page deep in the book, and confirm
text sits comfortably inside the margin with visible buffer — not touching
the edge.

**Never report a fix as done without re-rendering the actual page in
question.** Assuming a numeric fix worked without visual confirmation is
the single biggest time-waster observed building this pipeline.

### 4. Compute and build the cover — using the FINAL page count

```bash
python3 scripts/compute_cover_spec.py --pages <final_page_count_from_step_2>
python3 scripts/build_paperback_cover.py --config book_config.json --pages <final_page_count> --out cover.pdf
```

**If the interior changes again for any reason — including a spacing-only
fix that shifts page count by a few pages — rebuild the cover.** This is
the single most common late-stage KDP error (gotcha #6): "expected cover
size X but submitted file size Y," and it means exactly this, every time.

### 5. Kindle eBook (if requested)

```bash
python3 scripts/build_kindle_ebook.py --config book_config.json --out kindle_ebook.docx
python3 scripts/build_kindle_cover.py --config book_config.json --out kindle_cover.jpg
```

These are genuinely separate deliverables from the paperback files, not
derived from them — see `references/kdp-formatting-spec.md` for exactly
how the specs diverge (reflowable vs. fixed layout, front-only vs.
wraparound cover, no ISBN needed, different cover ratio).

### 6. Listing metadata

Draft description/categories/keywords per `references/listing-metadata.md`.
Present as a draft for the user to approve or edit, not a fait accompli —
these are subjective and worth a quick confirm.

## Diagnosing a KDP rejection message

If the user pastes an error instead of asking to build from scratch:

| Error text contains | Likely cause | Where to look |
|---|---|---|
| "Insufficient gutter" | Missing hyphenation, or emergencystretch not set | gotchas #1, #2, #8 |
| "text is outside the margins" | Blockquote/callout environment margins, or a specific unbreakable token | gotchas #5, #7 |
| "expected cover size ... but submitted" | Cover built for a stale page count | gotcha #6 |
| "removed non-printable markup ... check these pages" | Routine notice, usually the TOC — not a real error | gotcha #9 |

Get the exact flagged page numbers from the user, render them with
`verify_pages.py`, and check odd/even (gotcha #8) before assuming the fix
needed is content-specific rather than structural.

## Reference files

- `references/kdp-formatting-spec.md` — the actual KDP requirements (margins
  by page count, front/back matter order, cover formula, Kindle spec).
- `references/common-gotchas.md` — **read this before debugging any margin
  or overflow error** — every entry is a real bug found and fixed, not a
  hypothetical.
- `references/listing-metadata.md` — description/categories/keywords guidance.

## Assets

- `assets/kdp_template.tex` — the working, debugged LaTeX template. Has
  `$TRIM_WIDTH$`, `$TRIM_HEIGHT$`, `$GUTTER$`, `$OUTER$`, `$TOPBOTTOM$`
  placeholders for `build_kdp_interior.py` to fill in.
- `assets/front_matter_template.tex` — half-title/title/copyright/dedication
  pages template with the right-facing-page logic already correct.

## A note on scope

This skill assumes a standard nonfiction-style trade paperback (chapters,
front matter, optional appendix/toolkit). Fiction, illustrated books, and
technical books with heavy tables/code will need adaptation — the
front/back-matter ordering and margin math still apply, but the body
typesetting choices (image placement, code blocks, verse) are out of scope
for the current templates.
