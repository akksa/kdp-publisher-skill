# KDP Paperback Formatting Spec

Source of truth: fetch https://kdp.amazon.com/en_US/help/topic/GDDYZG2C7RVF5N9J
(Format Front Matter, Body Matter, and Back Matter) fresh at the start of any
job — Amazon updates this occasionally and this file may drift.

## Margins by page count (gutter/inside margin)

| Page count | Minimum inside margin (gutter) | Minimum outside/top/bottom |
|---|---|---|
| 24–150 | 0.375" | 0.25" |
| 151–300 | 0.5" | 0.25" |
| 301–500 | 0.625" | 0.25" |
| 501–700 | 0.75" | 0.25" |
| 701–828 | 0.875" | 0.25" |

**Always build with a real safety buffer above the minimum** — see
`references/common-gotchas.md` for why the stated minimum is not safe to
target exactly. In practice: use gutter = minimum + 0.25"–0.4" depending on
how much prose (vs. tables/forms) the book has.

## Front matter order (right/left facing rules)

In order, each with its required facing page:

1. **Half-title** — title only, no subtitle, no author. Right-facing page. No page number, no header.
2. **Title page** — full title, subtitle, author. Right-facing page, directly after half-title (forces a blank left page in between if needed).
3. **Copyright page** — first LEFT-facing page after the title page (i.e. the very next page — do not force it right).
4. **Dedication** (optional) — right-facing page.
5. **Table of contents** — right-facing page. No page number, no header.
6. **Preface / Acknowledgments / Prologue / Introduction** (optional, in that order if multiple present) — roman numeral page numbers, standard headers allowed.

Front matter uses lowercase roman numerals (i, ii, iii...). Body matter
resets to Arabic 1 at Chapter 1, which must start on a right-facing page.

## Body matter

- Left-page running header: author name. Right-page running header: book title. (Not chapter titles.)
- Chapter opening pages: no header, no running page number is conventional (not required, but standard).
- Paragraphs: indented, no blank line between paragraphs. **First paragraph after a heading has no first-line indent.**
- Fully justified body text.
- Every chapter starts on a right-facing (recto) page.

## Back matter

- Starts on a right-facing page.
- Bibliography/sources and author bio each conventionally start their own right-facing page.

## Cover (paperback, full wraparound PDF)

Spine width formula (black & white interior):
- **White paper**: `page_count * 0.002252` inches
- **Cream paper**: `page_count * 0.0025` inches

Full cover canvas:
```
cover_width  = bleed + back_cover_width + spine_width + front_cover_width + bleed
             = 0.125 + trim_width + spine_width + trim_width + 0.125
cover_height = bleed + trim_height + bleed
```
Bleed is always 0.125" per edge. At 300 DPI, multiply every inch figure by 300 for pixel dimensions.

Text/graphics on front and back cover must stay ≥0.125" inside the trim line
(use ≥0.25" for real safety margin). Spine text requires ≥0.0625" clearance
from each spine edge and needs at least 79 pages to be eligible at all.

Leave the bottom-right ~2"×1.2" of the back cover **completely blank** (no
border, no placeholder box) unless supplying your own barcode — KDP places
one there automatically.

**The cover must be rebuilt any time the interior page count changes**, even
by a few pages — the spine width is a direct function of page count. This is
one of the most common late-stage KDP rejection causes: a cover sized for an
earlier page count.

## Kindle eBook (separate deliverable, separate spec)

- Interior: reflowable, not fixed-page. Deliver as DOCX (or EPUB), not PDF.
  Kindle's own converter builds device-appropriate pagination from this.
- Navigation: comes automatically from Word "Heading 1" styles — do not rely
  on a manual Table of Contents field; it's fragile through the conversion
  pipeline. A visible in-book contents page is optional, not required for
  navigation to work.
- No ISBN required — Kindle eBooks get a free ASIN automatically.
- Cover: **single front-only image**, not a wraparound. JPEG (TIFF also ok),
  RGB (never CMYK), ideal size 1600×2560px (exactly 1.6:1 ratio), minimum
  1000px on the long side, 300 DPI recommended, under 50MB (never actually a
  constraint at reasonable quality settings).
- Every format (paperback, Kindle) has independent Categories (up to 3) and
  Keywords (7 fields, 50 chars each) in the KDP dashboard — fill in both if
  publishing both formats.
