# Manim pitfalls and their fixes

These came up while making earlier videos with manim CE 0.22. Each one cost a render round to
find.

## Crashes

- **`Text("")` crashes `align_to` and `next_to`** with `IndexError: too many indices for
  array`, because empty text has no points. Use `VGroup()` for an empty cell:
  `T(note) if note else VGroup()`.
- **`from manim import *` shadows names.** Do not name a variable `T`, `M`, `box`, `arrow`,
  `lines`, `code` or `frame` in a scene, or you will overwrite a helper. Also avoid `UP`, `DOWN`,
  `LEFT`, `RIGHT`, `ORIGIN`, `PI` and `TAU`.

## Things that render wrong without an error

- **Text morphing garbles the letters.** `Transform(text_a, text_b)` moves glyph outlines
  into one another and the middle frames are unreadable. Use `FadeTransform(a, b)` for any
  change of words. Keep `Transform` for shapes, or for a number that is replaced in place.
- **`FadeIn` and `Indicate` on one object in a single `play` leave it invisible.** Play them
  one after the other.
- **`set_opacity` on a filled box can brighten it**, because it sets the fill opacity too,
  usually above the box's 0.2–0.3. Use `m.animate.fade(0.6)` to dim something.
- **Leading spaces do not indent.** Lines are aligned by their visible glyphs. Use `code()`,
  which swaps spaces for non-breaking ones.
- **Two `.animate` on one object: only the last one counts.** An `.animate` computes its target from
  the object as it is when you write it, and the object keeps a single target. So
  `play(m.animate.shift(RIGHT), m.animate.set_color(RED))` recolors `m` but does not move it, and an
  `.animate` written before another `.animate` on the same object, and played after it, does
  nothing. Chain the changes in one: `m.animate.shift(RIGHT).set_color(RED)`, and write each
  `.animate` in the `play` (or `say(..., anims=...)`) that runs it.
- **Noto Sans has no math symbols.** ⊤ ⊥ ≤ ≥ ≠ ≈ → ⇒ ∈ ∞ ∀ ⌊ ⌋ and the minus sign − are missing from
  it, and so are ✓ and ✗. Pango draws a missing glyph from another font without a warning (Nimbus
  Sans, Noto Sans Mono or Noto Sans Symbols2), often in a different weight and size. Most of the
  time this is harmless. When the symbol carries meaning, and above all when it could be read as a
  letter (⊤ next to a timeout called T), draw it on its own in the math font:
  `T("⊤", 26, PURPLE_B, font="Noto Sans Math")`. That font has all of the above but ✓ and ✗.
- **The wrong object stays on screen after a transform.** After `ReplacementTransform(a, b)`
  or `FadeTransform(a, b)`, the scene holds `b`. After `Transform(a, b)`, it holds `a`, which now
  looks like `b`, and `b` was never added. If you animate the wrong one later, a ghost stays on
  screen, or nothing happens.
- **Something fades out at scene end that you meant to keep.** `clear_all()` fades every
  object in the scene. To clear the stage in the middle of a scene and keep the badge, use
  `clear_except(badge_obj)`.
- **A moving object hides labels.** A dot or token animated along a path passes over the box
  labels. Route it above the boxes, or fade the labels down while it moves.

## Layout

- **Text past x ≈ ±6.9 or y ≈ 3.85 is clipped.** The frame is 14.2 × 8 units. The check
  reports it.
- **The bottom 0.85 units belong to the caption.** Anything below y −3.15 collides with it.
  The check reports it.
- **Long labels inside fixed boxes.** `box()` fits the label to the box width, which can make
  it tiny. The check warns below 75% shrink and below 14 pt. Widen the box or shorten the label;
  do not just accept the shrink.
- **Rows that do not line up.** `arrange()` centres items, so columns of mixed widths look
  ragged. Use `place_row(items, xs, y)` for tables, or `arrange(aligned_edge=UP or LEFT)`.
- **Highlight boxes cut neighbouring lines.** In a stack of lines `buff=0.1` apart, a
  `SurroundingRectangle(line, buff=0.12)` crosses the lines above and below it. Keep the
  buff below half the gap, or highlight with a filled `BackgroundRectangle` behind the line.
  Boxes in one column should share one width: build `Rectangle(width=W, height=h)` and move it
  to each line, rather than wrapping each line separately.
- **Symbols that read two ways.** A ✓ or ✗ beside a word like "rejected" or "fails" can mean
  "this happens" or "this is right". Write the outcome in words ("passes", "rejected,
  wrongly"), or label what the mark means.
- **Brace labels overlap** when adjacent braces are short. Shorten the labels ("second cover",
  "no branches"), or put more space between the items.
- **Arrow tips the size of the arrow.** Manim scales tips with length. `arrow()` keeps them a
  fixed size.
- **Squares that move into a row drift**, when a cell is a square with a label below it.
  Move each cell by its square's centre: `cell.animate.shift(target - cell[0].get_center())`.

## Rendering

- Render with `--disable_caching`. Manim's cache sometimes reuses a stale partial movie
  after an edit.
- Re-render only the scenes you changed: `./pv.sh low topic.py S04Keys S09Sets`.
- `pv.sh low` builds contact sheets only for the scenes it rendered. `./pv.sh sheets topic.py`
  rebuilds all of them, using the frame times the last `low` render recorded.
- `pv.sh check` runs the scenes without writing video. It is only somewhat faster than `low`, so
  use it on one or two scenes while editing, not as a separate pass over the whole video.
- The final render (`pv.sh high`) renders every scene at 1080p60 and joins them in the order
  they appear in the file. Rename or reorder classes in the file to change the order. There is
  no separate list to keep in sync.
- A first render prints `INFO` lines from manim, and LaTeX output if you use `Tex`. Read only
  the `LAYOUT` lines and the Python tracebacks.
