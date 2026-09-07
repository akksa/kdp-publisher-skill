# Common Gotchas — Read Before Debugging From Scratch

Every one of these was discovered the hard way, through real KDP rejections.
If a KDP "insufficient gutter" or "text outside margins" error appears,
check these **in order** before assuming the margin numbers themselves are
wrong — in practice the margin numbers are usually fine and one of these is
the real cause.

## 1. Missing hyphenation (the #1 cause of margin violations)

XeLaTeX does not ship with English hyphenation patterns loaded by default,
and this environment in particular may not have them installed at all. With
no hyphenation, any long word that doesn't fit a line **overflows the
margin instead of breaking**, and on left-facing (even) pages that overflow
runs directly into the gutter.

**Symptom:** KDP flags "insufficient gutter" on a small, consistent set of
pages — and they're often specifically even-numbered pages, because
justified-text overflow drifts right, and the gutter is on the right side
of even pages in a twoside layout.

**Fix, in order:**
```bash
apt-get install -y texlive-lang-english
mktexlsr   # <-- do not skip this. apt's postinst hook does not always
           # register the new pattern files in TeX's search database.
           # Verify with: kpsewhich hyph-en-us.tex
           # If that returns nothing, the patterns are NOT actually loaded
           # yet even though the package is "installed."
```
In the LaTeX preamble:
```latex
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{english}
\setmainfont{DejaVu Serif}
```
**Verify before trusting it** — render a short isolated test with a
polysyllabic word in a narrow column and visually confirm actual hyphen
breaks appear (`trans-formation`, not the whole word pushed to the next
line or overflowing). Do not just check that pandoc/xelatex ran without
error — a silently-not-loaded pattern file produces no error, just bad
output.

## 2. The real, durable fix: emergencystretch (do this even after fixing hyphenation)

Hyphenation alone does not guarantee zero overfull boxes — some words,
formatting combinations, and short lines still won't fit even with correct
hyphenation. Chasing every individual overfull warning is a losing,
unbounded game (confirmed empirically: dozens of individually-fixed
overflows, and the total count barely moved, because fixing one line's
wrapping shifts the break point and can create a new overflow two lines
later).

**The actual fix** — add to the preamble:
```latex
\tolerance=9999
\emergencystretch=3em
\hbadness=10000
```
This tells LaTeX to add extra stretchable space between words rather than
let a line overflow when it's hard to break well. In the case this skill
was built from, this dropped overfull warnings from 200+ (worst case ~0.5")
down to 1 warning at 0.005" — a rounding artifact, not a real defect.
**Do this early**, not as a last resort after manually patching individual
words — it would have saved dozens of debugging cycles.

## 3. Do NOT "fix" margin violations by just widening margins

Counterintuitive but confirmed repeatedly: widening the margins narrows the
text column, and a narrower column makes wrapping *harder*, which increases
overflow, not decreases it. Margin-widening as a blanket fix is a
self-defeating cycle — each round shifts which specific words overflow and
sometimes produces a *worse* worst-case than before. Fix the wrapping
mechanism (item 2 above) first. Only touch margins after emergencystretch
is in place and you've confirmed via rendering that overflow is genuinely
near zero.

## 4. Inline raw LaTeX needs different syntax than block raw LaTeX

If generating LaTeX from Markdown via pandoc and inserting raw LaTeX
snippets (e.g. `\rule{}{}` fill-in lines, custom spacing):

- **Block-level** (its own paragraph, blank lines before/after):
  ` ```{=latex}` on its own line, content, ` ``` ` on its own line. This
  works.
- **Inline** (mid-sentence, same line as other text): the triple-backtick
  block syntax does **not** work inline — it renders as a literal escaped
  code span (`\texttt{...}` with every backslash shown as text). Use
  single-backtick inline raw syntax instead: `` `\rule{2in}{0.4pt}`{=latex} ``
  (backticks around the LaTeX, `{=latex}` immediately after the closing
  backtick, no space).

**Always test raw LaTeX snippets in a 5-line isolated `.tex` file before
trusting them in the full document** — a wrong syntax choice fails silently
(no compile error) and just produces garbage output, or in the block-used-
where-inline-was-needed direction, can create severe overfull boxes (one
confirmed case: two `\rule{\linewidth}{...}` elements separated only by
`\vspace` — not a real paragraph break — tried to occupy the same
horizontal line, demanding 2× the available width and overflowing ~5
inches). If chaining multiple `\rule{\linewidth}` elements vertically, put
`\par` before each `\vspace`, or better, give each its own paragraph
(blank line before and after) entirely.

## 5. Certain characters silently break hyphenation for the whole word/token

Confirmed via isolated testing, not guessed:

- **Forward slash** (`value/method`, `win/loss`) — XeTeX does not treat `/`
  as a valid break point, so the whole slash-joined string becomes one
  unbreakable token. **Fix: add a space on at least one side** (`value /
  method`), or the token can overflow a narrow column even with
  hyphenation patterns correctly loaded.
- This was tested and confirmed to be the *specific* cause of one 48pt
  (0.67") overflow that persisted through multiple rounds of unrelated
  fixes — margin changes did not affect it because it was never a margin
  problem.

If a specific overfull warning persists after emergencystretch is in place
and stays at an identical point-value across unrelated changes, that
exact-repetition is itself a clue: isolate the specific paragraph in a
standalone test file, then remove pieces one at a time until the warning
disappears. Whatever you removed last is the cause. This is faster and more
reliable than guessing.

## 6. Cover size must match interior page count exactly

If the interior is edited after the cover is built (even a spacing fix that
only shifts page count by a few pages, like the emergencystretch fix
above), KDP will reject the cover with an expected-vs-submitted size
mismatch. **Any interior edit that changes page count requires a cover
rebuild.** Recompute spine width from the *current* page count before
regenerating.

## 7. Blockquote / callout box environments need explicit margins

LaTeX's default `quote` environment margin can be too thin to reliably
clear KDP's automated margin checker, especially combined with hyphenation
edge cases inside the box. Set explicit left/right margins:
```latex
\renewenvironment{quote}{\list{}{\leftmargin1.2em\rightmargin1.2em}\item[]}{\endlist}
```

## 8. "Insufficient gutter" errors cluster on even pages — check odd/even, not just page number

In a twoside layout, the gutter (spine-side margin) is on the **right**
edge of even (left-facing) pages and the **left** edge of odd (right-facing)
pages. Justified-text overflow drifts right. So overflow on an even page
goes straight into the gutter; overflow on an odd page goes into the
(usually more generous) outer margin. If KDP flags a specific, small,
recurring set of pages, check whether they're all even — if so, the
remaining-margin arithmetic (`gutter_margin − worst_case_overflow`) is the
real diagnostic, not a vague sense that "something's still wrong."

## 9. The "Review: non-printable markup removed" notice is routine, not an error

KDP strips internal PDF structures (hyperlink anchors, bookmark trees) during
processing and flags the affected pages for a visual sanity check. This is
almost always the table of contents. Render the flagged pages and confirm
they still look right — this is not a quality-standard failure and doesn't
block publishing on its own.
