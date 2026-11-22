"""House style and helpers for 3Blue1Brown-style PR explainer videos (tested with manim CE 0.22).

Import it from the scene file with `from pr3b1b import *`. It re-exports manim.
Set PV_CHECK=1 (pv.sh check does) to print LAYOUT warnings while scenes run, and to write every caption and
on-screen text of a scene to sheets/text/<Scene>.txt (pv.sh text prints them).
"""

import os

import numpy as np
from manim import *  # noqa: F401,F403  (re-exported to the scene file)

config.background_color = "#14161b"

SANS = "Noto Sans"
MONO = "Noto Mono"

# Semantic colors shared by every video. Domain roles (C_CACHE = TEAL_C, C_COST = ORANGE ...) are
# defined in the scene file, one meaning per color, with a legend the first time it matters.
C_OK = GREEN_C
C_BAD = RED_C
C_WARN = YELLOW_C
C_DIM = GREY_B
C_TEXT2 = GREY_A

CHECK = bool(os.environ.get("PV_CHECK"))

# Safe area. Manim's frame is 14.22 x 8 units, centred on the origin.
SAFE_X = config.frame_width / 2 - 0.2
SAFE_TOP = config.frame_height / 2 - 0.15
CAPTION_TOP = -3.15  # content must stay above this line; the caption lives below it
MIN_FONT = 14  # hard floor; aim for 18+ for body text and 16+ for labels
TEXT_GAP = 0.06  # texts closer than this count as touching

_warned = set()


def _warn(msg, key=None):
    """Print one LAYOUT line per problem; key dedupes a problem that persists over many plays."""
    key = key or msg
    if CHECK and key not in _warned:
        _warned.add(key)
        print(f"LAYOUT {msg}", flush=True)


def _label(m):
    for x in m.get_family():
        if isinstance(x, Text):
            s = getattr(x, "original_text", None) or getattr(x, "text", "")
            return repr(s[:50])
    return type(m).__name__


# ---------------------------------------------------------------------------- text
def T(s, size=28, color=WHITE, font=SANS, **kw):
    """Sans text."""
    return Text(s, font=font, font_size=size, color=color, **kw)


def M(s, size=22, color=WHITE, **kw):
    """Monospace text, for identifiers, paths, flags and values from the code."""
    return Text(s, font=MONO, font_size=size, color=color, **kw)


def fit(m, w):
    """Shrink m to width w if it is wider. Warns when the text would end up too small to read."""
    if m.width > w:
        f = w / m.width
        if f < 0.75:
            _warn(f"fit shrinks {_label(m)} to {f:.0%}: shorten it or split it")
        m.scale_to_fit_width(w)
    return m


def lines(items, size=22, color=WHITE, buff=0.18, font=SANS):
    """Left-aligned stack of text lines."""
    return VGroup(*[T(s, size, color, font=font) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def code(src_lines, size=20, color=WHITE, buff=0.1):
    """Monospace block that keeps leading indentation and blank lines. Items may be (line, color)."""
    adv = M("0" * 20, size).width / 20  # one monospace advance
    line_h = M("Ag", size).height
    rows = []
    for s in src_lines:
        c = color
        if isinstance(s, tuple):
            s, c = s
        indent = len(s) - len(s.lstrip(" "))
        body = s.strip(" ")
        t = M(body, size, c) if body else Rectangle(width=0.01, height=line_h, stroke_opacity=0, fill_opacity=0)
        rows.append((t, indent))
    g = VGroup(*[t for t, _ in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    for t, indent in rows:
        t.shift(RIGHT * indent * adv)
    return g


# ---------------------------------------------------------------------------- shapes
def box(label, color, w=3.2, h=0.7, size=24, fill=0.25, mono=False, text_color=WHITE):
    """Rounded box with a one-line label."""
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, color=color,
                         fill_color=color, fill_opacity=fill, stroke_width=2.5)
    t = fit((M if mono else T)(label, size=size, color=text_color), w - 0.25)
    return VGroup(r, t.move_to(r))


def box2(top, bottom, color, w=3.2, h=0.85, size=22, sub=16, fill=0.2, mono_top=False):
    """Rounded box with a title and a grey subtitle."""
    r = RoundedRectangle(corner_radius=0.1, width=w, height=h, color=color,
                         fill_color=color, fill_opacity=fill, stroke_width=2.5)
    a = fit((M if mono_top else T)(top, size, WHITE), w - 0.25)
    b = fit(T(bottom, sub, C_TEXT2), w - 0.25)
    return VGroup(r, VGroup(a, b).arrange(DOWN, buff=0.08).move_to(r))


def chip(label, color, size=20, mono=True):
    """Small tag around a label: a fact, a value, a file, a status."""
    t = (M if mono else T)(label, size=size, color=color)
    r = SurroundingRectangle(t, buff=0.1, corner_radius=0.08, color=color,
                             stroke_width=2, fill_color=color, fill_opacity=0.12)
    return VGroup(r, t)


def frame(mobs, color=GREY_B, title=None, buff=0.25):
    """A labelled container drawn around existing mobjects (a process, a container, a module)."""
    r = SurroundingRectangle(mobs, buff=buff, corner_radius=0.12, color=color, stroke_width=2)
    if title is None:
        return VGroup(r)
    lab = T(title, 18, color).next_to(r, UP, buff=0.1).align_to(r, LEFT)
    return VGroup(r, lab)


def legend(items, size=18):
    """Color key: items is [(color, meaning), ...]."""
    return VGroup(*[VGroup(Square(0.25, color=c, fill_color=c, fill_opacity=0.4), T(s, size)).arrange(RIGHT, buff=0.15)
                    for c, s in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.12)


def badge(k, title):
    """Scene number and title, top left. Add it first in every scene but the intro."""
    num = T(f"{k}", 26, YELLOW, weight=BOLD)
    ttl = T(title, 26, C_DIM)
    return VGroup(num, ttl).arrange(RIGHT, buff=0.25).to_corner(UL, buff=0.4)


def arrow(p, q, color=GREY_B, sw=3, buff=0.08, tip=0.18):
    """Arrow whose tip stays the same size however short or long it is."""
    p, q = np.array(p, dtype=float), np.array(q, dtype=float)
    length = max(np.linalg.norm(q - p) - 2 * buff, 0.05)
    return Arrow(p, q, buff=buff, color=color, stroke_width=sw,
                 max_tip_length_to_length_ratio=min(0.6, tip / length),
                 max_stroke_width_to_length_ratio=20)


def strike(m, color=C_BAD):
    """Line through a mobject: removed, excluded, not in the key. The layout check expects it to cross text."""
    line = Line(m.get_left() + LEFT * 0.06, m.get_right() + RIGHT * 0.06, color=color, stroke_width=3)
    line.crosses_text = True
    return line


def bars(heights, color, w=0.2, scale=0.8):
    """A tiny bar chart, bottoms aligned."""
    g = VGroup(*[Rectangle(width=w, height=h * scale, color=color, fill_color=color, fill_opacity=0.6,
                           stroke_width=1.5) for h in heights])
    return g.arrange(RIGHT, buff=0.06, aligned_edge=DOWN)


def place_row(mobs, xs, y):
    """Put each mobject's left edge at xs[i], all centred on height y: table columns."""
    for m, x in zip(mobs, xs):
        m.move_to([0, y, 0]).align_to([x, 0, 0], LEFT)
    return VGroup(*mobs)


# ---------------------------------------------------------------------------- scene
class Captioned(Scene):
    """A scene with one subtitle line at the bottom, replaced in place by say()."""

    def setup(self):
        self.caption = None
        self._beats = []
        self._captions = []  # (time, text) of every caption, in order
        self._texts = {}  # every other text shown -> when it first appeared

    def tear_down(self):
        if CHECK:
            name = type(self).__name__
            os.makedirs("sheets/beats", exist_ok=True)
            with open(f"sheets/beats/{name}.txt", "w") as f:
                beats = [t for i, t in enumerate(self._beats) if i == 0 or t - self._beats[i - 1] > 0.3]
                f.write("\n".join(f"{t:.3f}" for t in beats) + "\n")
            # Everything the viewer reads, so that each number and name can be checked against facts.md.
            os.makedirs("sheets/text", exist_ok=True)
            with open(f"sheets/text/{name}.txt", "w") as f:
                f.write(f"== {name} ({self.renderer.time:.1f} s)\ncaptions:\n")
                f.writelines(f"  {t:6.1f}  {s}\n" for t, s in self._captions)
                f.write("on screen:\n")
                f.writelines(f"  {t:6.1f}  {s}\n" for s, t in self._texts.items())

    def wait(self, duration=DEFAULT_WAIT_TIME, *args, **kwargs):
        super().wait(duration, *args, **kwargs)
        # The end of each hold is a settled picture: the contact sheets take their frames there.
        if duration >= 0.5:
            self._beats.append(self.renderer.time)

    def say(self, text, wait=None, size=26, *, anims=(), run_time=None):
        """Show text as the caption, then hold it. wait defaults to reading time.

        anims play together with the caption change, so a step and the caption about it arrive at once.
        """
        new = T(text, size, C_TEXT2)
        if new.width > 13:
            if 13 / new.width < 0.75:
                _warn(f"{type(self).__name__}: caption shrunk to {13 / new.width:.0%}, split it: {text[:60]!r}")
            new.scale_to_fit_width(13)
        new.to_edge(DOWN, buff=0.4)
        new.is_caption = True
        self._captions.append((self.renderer.time, text))
        swap = [FadeIn(new, shift=0.15 * UP)]
        if self.caption is not None:
            swap.insert(0, FadeOut(self.caption, shift=0.15 * UP))
        if run_time:
            timing = {"run_time": run_time}
        elif anims:
            timing = {}  # each animation keeps its own run_time
        else:
            timing = {"run_time": 0.6}
        self.play(*swap, *anims, **timing)
        self.caption = new
        self.wait(wait if wait is not None else max(1.4, min(4.0, len(text) / 28)))

    def drop_caption(self):
        if self.caption is not None:
            self.play(FadeOut(self.caption), run_time=0.4)
            self.caption = None

    def clear_all(self, run_time=0.8):
        """Fade out everything, caption included. End every scene with it."""
        self._beats.append(self.renderer.time)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)
        self.caption = None

    def clear_except(self, *keep, run_time=0.6):
        """Fade out everything but the caption and the given mobjects (e.g. the badge)."""
        keep = set(keep) | {self.caption}
        gone = [m for m in self.mobjects if m not in keep]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=run_time)

    # ------------------------------------------------------------------ layout check
    def play(self, *args, **kwargs):
        start = self.renderer.time
        super().play(*args, **kwargs)
        if CHECK and not all(isinstance(a, Wait) for a in args):
            self._check_layout(start)

    def _check_layout(self, start=0.0):
        name = type(self).__name__
        t = self.renderer.time
        cap = set()
        for top in self.mobjects:
            if getattr(top, "is_caption", False):
                cap |= set(top.get_family())
        texts, shapes = [], []
        for top in self.mobjects:
            if top in cap:
                continue
            glyphs = set()
            for m in top.get_family():
                if isinstance(m, Text) and _visible_fill(m) > 0.05:
                    texts.append(m)
                if isinstance(m, Text):
                    glyphs |= set(m.get_family())
            for m in top.get_family():
                if not m.has_points() or max(m.get_fill_opacity(), m.get_stroke_opacity()) < 0.05:
                    continue
                lo, hi = m.get_corner(DL), m.get_corner(UR)
                if lo[0] < -SAFE_X - 1e-3 or hi[0] > SAFE_X + 1e-3 or hi[1] > SAFE_TOP + 1e-3:
                    _warn(f"{name} t={t:.1f}s: {_label(top)} leaves the frame "
                          f"(x {lo[0]:.2f}..{hi[0]:.2f}, top {hi[1]:.2f})", (name, "frame", _label(top)))
                if lo[1] < CAPTION_TOP:
                    _warn(f"{name} t={t:.1f}s: {_label(top)} reaches into the caption band (bottom {lo[1]:.2f})",
                          (name, "band", _label(top)))
                if m not in glyphs and isinstance(m, VMobject) and not getattr(m, "crosses_text", False) \
                        and m.get_stroke_width() >= 0.5 and m.get_stroke_opacity() >= 0.05:
                    shapes.append((m, top))
        for m in texts:
            s = getattr(m, "original_text", None) or getattr(m, "text", "")
            self._texts.setdefault(" / ".join(s.split("\n")), start)
        for m in texts:
            if m.font_size < MIN_FONT - 0.5:
                _warn(f"{name} t={t:.1f}s: {_label(m)} is {m.font_size:.0f}pt, too small to read",
                      (name, "small", _label(m)))
        boxes = [(m, m.get_corner(DL), m.get_corner(UR)) for m in texts]
        g = TEXT_GAP / 2
        for i, (a, alo, ahi) in enumerate(boxes):
            for b, blo, bhi in boxes[i + 1:]:
                if min(ahi[0], bhi[0]) - max(alo[0], blo[0]) > -2 * g and \
                        min(ahi[1], bhi[1]) - max(alo[1], blo[1]) > -2 * g:
                    _warn(f"{name} t={t:.1f}s: {_label(a)} overlaps or touches {_label(b)}",
                          (name, "overlap", _label(a), _label(b)))
        # A stroke (line, arrow, box edge) passing through the middle of a text.
        inner = [(m, lo + 0.015, hi - 0.015) for m, lo, hi in boxes]
        for m, top in shapes:
            mlo, mhi = m.get_corner(DL), m.get_corner(UR)
            near = [(x, lo, hi) for x, lo, hi in inner
                    if mlo[0] <= hi[0] and lo[0] <= mhi[0] and mlo[1] <= hi[1] and lo[1] <= mhi[1]]
            if not near:
                continue
            for p, q in _segments(m):
                hit = next((x for x, lo, hi in near if _seg_hits_box(p, q, lo, hi)), None)
                if hit is not None:
                    what = type(m).__name__ + ("" if top is m else f" in {_label(top)}")
                    _warn(f"{name} t={t:.1f}s: {what} crosses the text {_label(hit)}",
                          (name, "cross", _label(top), _label(hit)))
                    break


def _visible_fill(m):
    return max((s.get_fill_opacity() for s in m.family_members_with_points()), default=0)


def _segments(m):
    """Chords approximating each cubic Bezier curve of m: anchor to midpoint to anchor."""
    pts = m.points
    for i in range(0, len(pts) - 3, 4):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        mid = (p0 + 3 * p1 + 3 * p2 + p3) / 8
        yield p0, mid
        yield mid, p3


def _seg_hits_box(p, q, lo, hi):
    """Whether segment pq meets the axis-aligned box lo..hi (Liang-Barsky)."""
    t0, t1 = 0.0, 1.0
    for k in (0, 1):
        d = q[k] - p[k]
        if abs(d) < 1e-9:
            if p[k] < lo[k] or p[k] > hi[k]:
                return False
            continue
        a, b = (lo[k] - p[k]) / d, (hi[k] - p[k]) / d
        if a > b:
            a, b = b, a
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1:
            return False
    return True
