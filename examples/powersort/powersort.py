"""python/cpython#28108: list.sort() switches to the powersort merge order (Tim Peters, merged 2021-09-06).

A real PR, explained with the pr-explainer-video skill. Every figure on screen is in facts.md with its source.
The toy example is driven by powerloop() and powersort_trace(), line-for-line copies of the PR's C
functions, checked against the C itself (compiled from the PR's listobject.c) on random inputs.
"""

from pr3b1b import *

C_RUN = BLUE_C      # runs of the list
C_RUN2 = BLUE_D     # every other run, so neighbours read apart
C_MID = TEAL_C      # midpoints and the gap between them
C_POW = GOLD_C      # powers: levels of the merge tree
C_COST = ORANGE     # merge cost
C_OLD = RED_C       # the old rule
C_NEW = GREEN_C     # powersort


# ---------------------------------------------------------------------------- the PR's code, copied
def powerloop(s1, n1, n2, n):
    """Copy of powerloop() in Objects/listobject.c at the PR's head."""
    result = 0
    a = 2 * s1 + n1
    b = a + n1 + n2
    while True:
        result += 1
        if a >= n:
            a -= n
            b -= n
        elif b >= n:
            break
        a <<= 1
        b <<= 1
    return result


def powerloop_steps(s1, n1, n2, n):
    """The same loop, recording (a, b, bit of a/n, bit of b/n, next a, next b) at each turn."""
    a = 2 * s1 + n1
    b = a + n1 + n2
    steps = []
    while True:
        if a >= n:
            steps.append((a, b, 1, 1, (a - n) << 1, (b - n) << 1))
            a, b = (a - n) << 1, (b - n) << 1
        elif b >= n:
            steps.append((a, b, 0, 1, None, None))
            return steps
        else:
            steps.append((a, b, 0, 0, a << 1, b << 1))
            a, b = a << 1, b << 1


def powersort_trace(runs):
    """found_new_run() then the push, for each run; then merge_force_collapse() (unchanged by the PR)."""
    n = sum(runs)
    stack, ev, start = [], [], 0  # stack entries: [start, len, power]
    for n2 in runs:
        if stack:
            s1, n1, _ = stack[-1]
            power = powerloop(s1, n1, n2, n)
            ev.append(("power", len(stack) - 1, power))
            while len(stack) > 1 and stack[-2][2] > power:
                a, b = stack[-2], stack[-1]
                ev.append(("merge", len(stack) - 2, a[1], b[1]))
                stack[-2:] = [[a[0], a[1] + b[1], a[2]]]
            stack[-1][2] = power
        stack.append([start, n2, None])
        ev.append(("push", n2))
        start += n2
    while len(stack) > 1:
        i = len(stack) - 2
        if i > 0 and stack[i - 1][1] < stack[i + 1][1]:
            i -= 1
        a, b = stack[i], stack[i + 1]
        ev.append(("merge", i, a[1], b[1]))
        stack[i:i + 2] = [[a[0], a[1] + b[1], a[2]]]
    return ev


RUNS = [4, 6, 2, 5, 9, 3, 3]
N = sum(RUNS)
STARTS = [sum(RUNS[:i]) for i in range(len(RUNS))]
POWERS = [powerloop(STARTS[i], RUNS[i], RUNS[i + 1], N) for i in range(len(RUNS) - 1)]
TRACE = powersort_trace(RUNS)
COST = sum(e[2] + e[3] for e in TRACE if e[0] == "merge")
assert N == 32 and POWERS == [3, 2, 3, 1, 2, 3] and COST == 87  # facts.md, worked example
OLD_COST = 97  # the base's merge_collapse() on the same runs (harness.c, facts.md)


def X(k, x0=-6.4, unit=0.4):
    return x0 + unit * k


def run_bars(lengths, y, x0=-6.4, unit=0.4, h=0.45, size=20, gap=0.05):
    """One bar per run, laid end to end from x0, with its length inside."""
    out = VGroup()
    s = 0
    for i, n in enumerate(lengths):
        c = C_RUN if i % 2 == 0 else C_RUN2
        r = Rectangle(width=n * unit - gap, height=h, color=c, fill_color=c, fill_opacity=0.35, stroke_width=2)
        r.move_to([x0 + unit * (s + n / 2), y, 0])
        out.add(VGroup(r, T(str(n), size).move_to(r)))
        s += n
    return out


# ----------------------------------------------------------------------------
class S00Intro(Captioned):
    def construct(self):
        title = T("list.sort() learns powersort", 56, weight=BOLD)
        sub = T("python/cpython PR #28108 · Tim Peters · merged 6 September 2021", 24, C_DIM)
        chips = VGroup(chip("3 files", GREY_A, 20, mono=False), chip("+178  -92 lines", GREY_A, 20, mono=False),
                       chip("9 commits", GREY_A, 20, mono=False), chip("issue bpo-34561", GREY_A, 20, mono=False)
                       ).arrange(RIGHT, buff=0.3)
        VGroup(title, sub, chips).arrange(DOWN, buff=0.45).move_to(UP * 0.6)
        self.play(FadeIn(title, shift=0.2 * UP))
        self.say("This PR changes one decision inside Python's list.sort(): which runs to merge, and when.", 2.4,
                 anims=[FadeIn(sub)])
        self.say("It swaps the original home-made rule for powersort's, from a paper by Munro and Wild.", 2.4,
                 anims=[LaggedStart(*[FadeIn(c) for c in chips], lag_ratio=0.15)])
        self.say("This video shows the end state of the PR, as merged.", 1.8)
        self.clear_all()


# ----------------------------------------------------------------------------
class S01Runs(Captioned):
    def construct(self):
        bdg = badge(1, "how list.sort() merges")
        self.add(bdg)
        bars = run_bars(RUNS, 1.2)
        note = T("toy run lengths, n = 32", 18, C_DIM).move_to([0, 0.5, 0])
        self.say("list.sort() first cuts the list into runs: stretches that are already in order.", 2.2,
                 anims=[LaggedStart(*[FadeIn(b, shift=0.1 * RIGHT) for b in bars], lag_ratio=0.12)])
        self.say("Real runs are at least minrun long, 32 to 64 items. These lengths are toy units.", 2.2,
                 anims=[FadeIn(note)])
        pair = SurroundingRectangle(VGroup(bars[0], bars[1]), buff=0.1, color=C_WARN, stroke_width=2.5)
        self.say("Then it merges neighbouring runs, two at a time, until one run is left.", 2.0,
                 anims=[Create(pair)])
        self.play(FadeOut(VGroup(bars, note, pair)), run_time=0.6)

        head = T("cost of merging runs of lengths A and B:  A + B", 26).move_to(UP * 2.3)
        self.say("The PR's discussion counts merging runs of lengths A and B as costing A + B.", 2.4,
                 anims=[FadeIn(head)])

        def panel(x0, first, label_x):
            unit, h = 0.6, 0.42
            row1 = run_bars([1, 2, 3], 1.3, x0=x0, unit=unit, h=h)
            if first == (0, 1):
                mids = [3, 3]
                c1, c2 = 3, 6
            else:
                mids = [1, 5]
                c1, c2 = 5, 6
            row2 = run_bars(mids, 0.3, x0=x0, unit=unit, h=h)
            row3 = run_bars([6], -0.7, x0=x0, unit=unit, h=h)
            l2 = T(f"cost {c1}", 22, C_COST).move_to([label_x, 0.3, 0])
            l3 = T(f"cost {c2}", 22, C_COST).move_to([label_x, -0.7, 0])
            return row1, row2, row3, l2, l3, f"total {c1} + {c2} = {c1 + c2}"

        lr1, lr2, lr3, ll2, ll3, lt = panel(-6.2, (0, 1), -1.6)
        rr1, rr2, rr3, rl2, rl3, rt = panel(0.9, (1, 2), 5.7)
        assert lt.endswith("9") and rt.endswith("11")  # facts.md: 9 and 11
        ltot = T(lt, 24, C_NEW).move_to([-3.9, -1.75, 0])
        rtot = T(rt, 24, C_OLD).move_to([3.2, -1.75, 0])
        div = DashedLine([-0.2, 1.75, 0], [-0.2, -2.2, 0], color=GREY_D)
        self.play(FadeIn(lr1), FadeIn(rr1), Create(div))
        lsel = SurroundingRectangle(VGroup(lr1[0], lr1[1]), buff=0.08, color=C_WARN, stroke_width=2)
        self.say("Runs 1, 2 and 3: merge 1 and 2 first, then 3 and 3.", 1.8,
                 anims=[Create(lsel), FadeIn(lr2, shift=0.2 * DOWN), FadeIn(ll2)])
        self.play(FadeIn(lr3, shift=0.2 * DOWN), FadeIn(ll3), FadeOut(lsel))
        self.say("The total cost is 3 + 6 = 9.", 1.6, anims=[FadeIn(ltot)])
        rsel = SurroundingRectangle(VGroup(rr1[1], rr1[2]), buff=0.08, color=C_WARN, stroke_width=2)
        self.say("Merge 2 and 3 first, then 1 and 5, and it is 5 + 6 = 11.", 2.0,
                 anims=[Create(rsel), FadeIn(rr2, shift=0.2 * DOWN), FadeIn(rl2)])
        self.play(FadeIn(rr3, shift=0.2 * DOWN), FadeIn(rl3), FadeOut(rsel), FadeIn(rtot))
        self.say("The order of merges is all this PR changes: which neighbours, and when.", 2.2)
        self.say("The sort decides as it goes: each run it finds joins a stack of runs waiting to merge.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
class S02Before(Captioned):
    def construct(self):
        self.add(badge(2, "before: merge_collapse()"))
        names = ["older runs", "A", "B", "C"]
        stack = VGroup()
        for i, nm in enumerate(names):
            c = GREY_D if i == 0 else C_RUN
            b = box(nm, c, w=2.6, h=0.55, size=22 if i else 18, fill=0.2 if i else 0.1)
            stack.add(b.move_to([-4.3, -1.9 + 0.68 * i, 0]))
        top = T("top of the stack", 18, C_DIM).next_to(stack, UP, buff=0.2)
        rules = VGroup(
            VGroup(T("1", 26, C_POW), M("A > B + C", 26)).arrange(RIGHT, buff=0.35),
            VGroup(T("2", 26, C_POW), M("B > C", 26)).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([1.2, 1.2, 0]).align_to([-0.6, 0, 0], LEFT)
        self.say("Until now, merge_collapse() kept two rules on the three runs at the top of the stack.", 2.4,
                 anims=[LaggedStart(*[FadeIn(b, shift=0.1 * UP) for b in stack], lag_ratio=0.15), FadeIn(top)])
        self.say("A must be longer than B and C together, and B longer than C. A broken rule forces a merge.",
                 2.6, anims=[FadeIn(rules)])
        cap = VGroup(T("so lengths grow at least like Fibonacci numbers,", 20),
                     T("and the stack holds at most 85 runs (MAX_MERGE_PENDING)", 20)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([1.2, -0.35, 0])
        self.say("Read downward, the lengths grow at least like Fibonacci numbers: at most 85 pending runs.", 2.6,
                 anims=[FadeIn(cap)])
        self.play(FadeOut(VGroup(stack, top, rules, cap)), run_time=0.6)

        hist = VGroup(
            chip("the rules were subtle", GREY_A, 22, mono=False),
            chip("a computer-checked proof found them broken", C_OLD, 22, mono=False),
            chip("repaired, as the researchers suggested", C_NEW, 22, mono=False),
            chip("at least a dozen new merge strategies", GREY_A, 22, mono=False),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([-2.3, 1.0, 0]).align_to([-6.3, 0, 0], LEFT)
        self.say("The rules were subtle enough that they were not always kept.", 2.0,
                 anims=[FadeIn(hist[0]), FadeIn(hist[1])])
        self.say("Researchers found that while trying to complete a computer-checked correctness proof.", 2.4)
        self.say("It was repaired, and it set off research into better ways to merge on the fly.", 2.2,
                 anims=[FadeIn(hist[2]), FadeIn(hist[3])])
        paper = VGroup(
            T("Nearly-Optimal Mergesorts: Fast, Practical Sorting", 22),
            T("Methods That Optimally Adapt to Existing Runs", 22),
            T("J. Ian Munro and Sebastian Wild", 20, C_DIM),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        card = VGroup(SurroundingRectangle(paper, buff=0.3, corner_radius=0.12, color=C_NEW, stroke_width=2.5),
                      paper).move_to([0, -1.55, 0])
        tag = T("powersort", 24, C_NEW, weight=BOLD).next_to(card, RIGHT, buff=0.3).shift(UP * 0.2)
        tag2 = T("near-optimal,", 18, C_DIM).next_to(tag, DOWN, buff=0.12).align_to(tag, LEFT)
        tag3 = T("with proofs", 18, C_DIM).next_to(tag2, DOWN, buff=0.12).align_to(tag, LEFT)
        VGroup(card, tag, tag2, tag3).set_x(0)
        self.say("This PR adopts powersort, from Munro and Wild: provably near-optimal in its merge cost.", 2.6,
                 anims=[FadeIn(card), FadeIn(tag), FadeIn(tag2), FadeIn(tag3)])
        self.clear_all()


# ----------------------------------------------------------------------------
LEVEL_Y = {1: 2.1, 2: 1.3, 3: 0.5}
BAR_Y = -1.2
BAR_TOP = BAR_Y + 0.225


class S03Power(Captioned):
    def construct(self):
        self.add(badge(3, "a run's power"))
        bars = run_bars(RUNS, BAR_Y)
        ends = VGroup(T("0", 20, C_DIM).move_to([X(0), -1.75, 0]), T("32", 20, C_DIM).move_to([X(32), -1.75, 0]))
        self.say("Powersort sees the whole list as the interval from 0 to 1. Here it is 32 items long.", 2.4,
                 anims=[FadeIn(bars), FadeIn(ends)])

        ticks, fracs, lvls = {}, VGroup(), VGroup()
        for L, y in LEVEL_Y.items():
            step = 32 // 2 ** L
            for k in range(step, 32, 2 * step):
                ticks[k] = (L, Line([X(k), BAR_TOP + 0.03, 0], [X(k), y, 0], color=GOLD_E, stroke_width=2))
                num = k // step
                fracs.add(T(f"{num}/{2 ** L}", 18, C_POW).move_to([X(k), y + 0.25, 0]))
            lvls.add(T(f"level {L}", 18, C_DIM).move_to([-6.0, y, 0]))
        tick_g = VGroup(*[t for _, t in ticks.values()])
        self.say("Ticks cut it into halves, then quarters, then eighths: levels 1, 2 and 3.", 2.2,
                 anims=[LaggedStart(*[Create(t) for _, t in sorted(ticks.values(), key=lambda p: p[0])],
                                    lag_ratio=0.1), FadeIn(fracs), FadeIn(lvls)])

        mids = [STARTS[i] + RUNS[i] / 2 for i in range(len(RUNS))]
        dots = VGroup(*[Dot([X(m), BAR_TOP, 0], radius=0.07, color=C_MID) for m in mids])
        nodes = {}

        def gap(i):
            y = -0.55
            ln = Line([X(mids[i]), y, 0], [X(mids[i + 1]), y, 0], color=C_MID, stroke_width=4)
            caps = VGroup(Line([X(mids[i]), y - 0.1, 0], [X(mids[i]), y + 0.1, 0], color=C_MID, stroke_width=3),
                          Line([X(mids[i + 1]), y - 0.1, 0], [X(mids[i + 1]), y + 0.1, 0], color=C_MID,
                               stroke_width=3))
            return VGroup(ln, caps)

        def node(i):
            p = POWERS[i]
            k = next(k for k in sorted(ticks, key=lambda k: ticks[k][0]) if mids[i] < k <= mids[i + 1])
            assert ticks[k][0] == p
            nodes[i] = (k, Dot([X(k), LEVEL_Y[p], 0], radius=0.1, color=C_POW))
            return k

        g0 = gap(0)
        self.say("Each run has a midpoint. Take two neighbouring runs, and the gap between their midpoints.", 2.4,
                 anims=[FadeIn(dots), Create(g0)])
        k = node(0)
        self.say("The power is the first level with a tick in that gap: level 3, at 4/32 = 1/8.", 2.4,
                 anims=[ticks[k][1].animate.set_color(C_POW).set_stroke(width=4), FadeIn(nodes[0][1], scale=1.5)])
        g1 = gap(1)
        k = node(1)
        self.play(ReplacementTransform(g0, g1), run_time=0.6)
        self.say("Between the 6 and the 2, the first tick is at 8/32 = 1/4: power 2.", 2.2,
                 anims=[ticks[k][1].animate.set_color(C_POW).set_stroke(width=4), FadeIn(nodes[1][1], scale=1.5)])
        rest = []
        for i in range(2, 6):
            k = node(i)
            rest += [ticks[k][1].animate.set_color(C_POW).set_stroke(width=4), FadeIn(nodes[i][1], scale=1.5)]
        self.play(FadeOut(g1), run_time=0.4)
        self.say("The other four neighbours get powers 3, 1, 2 and 3.", 2.0, anims=[LaggedStart(*rest, lag_ratio=0.15)])

        # The tree the powers describe: each node joins the two subtrees on either side of it.
        def subtree(lo, hi):
            """Node index (pair) or leaf ("run", j) for runs lo..hi."""
            if lo == hi:
                return ("run", lo)
            i = min(range(lo, hi), key=lambda j: POWERS[j])
            return ("node", i, subtree(lo, i), subtree(i + 1, hi))

        def top_of(t):
            if t[0] == "run":
                return np.array([X(mids[t[1]]), BAR_TOP + 0.02, 0])
            k, d = nodes[t[1]]
            return d.get_center()

        edges = VGroup()

        def walk(t):
            if t[0] == "run":
                return
            p = top_of(t)
            for ch in t[2:]:
                edges.add(Line(p, top_of(ch), color=C_POW, stroke_width=2.5, buff=0.1))
                walk(ch)

        walk(subtree(0, len(RUNS) - 1))
        self.play(FadeOut(fracs), tick_g.animate.set_stroke(opacity=0.25), FadeOut(dots), run_time=0.6)
        self.say("Join each node to its neighbours below, and the powers draw a binary merge tree.", 2.4,
                 anims=[LaggedStart(*[Create(e) for e in edges], lag_ratio=0.08)])
        self.say("Power 1 is the root. A deeper node joins two runs that merge sooner.", 2.2)
        self.say("This is the order powersort aims for. It finds it one run at a time, as the sort scans.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
class S04Powerloop(Captioned):
    def construct(self):
        self.add(badge(4, "computing it: powerloop()"))
        src = [
            "a = 2 * s1 + n1;",
            "b = a + n1 + n2;",
            "for (;;) {",
            "    ++result;",
            "    if (a >= n) {",
            "        a -= n;",
            "        b -= n;",
            "    }",
            "    else if (b >= n) {",
            "        break;",
            "    }",
            "    a <<= 1;",
            "    b <<= 1;",
            "}",
        ]
        cb = code(src, 17).move_to([-4.1, -0.15, 0])
        cl = T("Objects/listobject.c, powerloop()", 18, C_DIM).next_to(cb, UP, buff=0.3).align_to(cb, LEFT)
        hl = Rectangle(width=5.0, height=0.34, stroke_width=0, fill_color=C_POW, fill_opacity=0.18)

        def at(*ranges):
            """One highlight per (first, last) range of code lines."""
            out = VGroup()
            for lo, hi in ranges:
                g = VGroup(*[cb[i] for i in range(lo, hi + 1)])
                out.add(hl.copy().stretch_to_fit_height(g.height + 0.12).move_to(g).align_to(cb, LEFT)
                        .shift(LEFT * 0.12))
            return out

        self.say("powerloop() finds the power without division or floating point.", 2.0,
                 anims=[FadeIn(cb), FadeIn(cl)])
        h = at((0, 1))
        self.add_foreground_mobject(cb)
        self.say("It doubles both midpoints so they are whole numbers: a = 2·s1 + n1, b = a + n1 + n2.", 2.6,
                 anims=[FadeIn(h)])

        s1, n1, n2 = STARTS[5], RUNS[5], RUNS[6]
        steps = powerloop_steps(s1, n1, n2, N)
        assert len(steps) == POWERS[5] == 3 and steps[0][:2] == (55, 61)
        inp = M(f"s1 = {s1}   n1 = {n1}   n2 = {n2}   n = {N}", 20, C_MID).move_to([3.0, 2.45, 0])
        xs = [-0.2, 0.7, 2.45, 3.9]
        hdr = place_row([T(t, 18, C_DIM) for t in ["turn", "a, b", "digits", "next a, b"]], xs, 1.75)
        self.say(f"Take the last two runs, 3 and 3, starting at {s1}: a = {steps[0][0]}, b = {steps[0][1]}, "
                 f"n = {N}.", 2.4, anims=[FadeIn(inp), FadeIn(hdr)])
        rows = VGroup()
        for t, (a, b, ba, bb, na, nb) in enumerate(steps):
            nxt = f"{na}, {nb}" if na is not None else f"stop: power {t + 1}"
            col = WHITE if na is not None else C_POW
            rows.add(place_row([M(str(t + 1), 20), M(f"{a}, {b}", 20), M(f"{ba} {bb}", 20, C_MID),
                                M(nxt, 18, col)], xs, 1.2 - 0.55 * t))
        caps = [
            "Each turn reads one binary digit of a/n and b/n. Both are 1: subtract n, then shift left.",
            f"Both 1 again: {steps[1][0]} and {steps[1][1]} become {steps[1][4]} and {steps[1][5]}.",
            "Now a is below n and b is not: the digits differ at position 3. The power is 3.",
        ]
        lines_for = [((4, 7), (11, 12)), ((4, 7), (11, 12)), ((8, 9),)]
        for t in range(3):
            nh = at(*lines_for[t])
            self.play(FadeOut(h), FadeIn(nh), run_time=0.4)
            h = nh
            self.say(caps[t], 2.6, anims=[FadeIn(rows[t], shift=0.1 * RIGHT)])

        def binary(lbl, digits):
            t = M(f"{lbl} = 0.{digits}", 22)
            k = len(lbl.replace(" ", "")) + 1 + 2 + 2  # glyphs before the third binary digit ("=", "0.", 2 digits)
            t[k].set_color(C_POW)
            return t, t[k]

        b1, d1 = binary("27.5 / 32", "110111")
        b2, d2 = binary("30.5 / 32", "111101")
        bins = VGroup(b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.0, -1.35, 0])
        bl = T("the midpoints, in binary", 18, C_DIM).next_to(bins, UP, buff=0.2).align_to(bins, LEFT)
        mark = Rectangle(width=d1.width + 0.16, height=abs(d1.get_top()[1] - d2.get_bottom()[1]) + 0.16,
                         stroke_width=0, fill_color=C_POW, fill_opacity=0.25).move_to(VGroup(d1, d2))
        self.say("In binary the midpoints are 0.110111 and 0.111101: they first differ at digit 3.", 2.6,
                 anims=[FadeIn(mark), FadeIn(bins), FadeIn(bl)])
        self.play(FadeOut(VGroup(inp, hdr, rows, bins, bl, mark, h)), run_time=0.6)
        why = VGroup(T("the paper's O(1) method needs", 20, C_DIM),
                     T("count leading zeros: no portable C spelling", 20),
                     T("division at twice the width of Py_ssize_t", 20),
                     T("the loop runs once per run: lost in the noise", 20, C_NEW)
                     ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to([2.9, 0.3, 0])
        self.say("The paper computes the power in O(1), but that needs a count-leading-zeros,", 2.2,
                 anims=[FadeIn(why[0]), FadeIn(why[1])])
        self.say("which has no portable C spelling, and division on integers twice as wide as Py_ssize_t.", 2.6,
                 anims=[FadeIn(why[2])])
        self.say("The loop runs once per run, and runs are rarely short, so its cost is lost in the noise.", 2.4,
                 anims=[FadeIn(why[3])])
        self.clear_all()


# ----------------------------------------------------------------------------
class S05Stack(Captioned):
    def construct(self):
        self.add(badge(5, "the merge rule: found_new_run()"))
        top = run_bars(RUNS, 2.4, h=0.4, size=18)
        self.play(FadeIn(top))
        rule = VGroup(T("when the sort finds a run:", 20, C_DIM),
                      T("1  compute the power of the run on top", 20),
                      T("2  merge while the run below is deeper", 20),
                      T("3  push the new run", 20)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        rule.move_to([2.6, 1.0, 0])
        cost_l = T("merge cost", 22, C_COST).move_to([2.0, -2.45, 0])
        cost_v = M("0", 24, C_COST).next_to(cost_l, RIGHT, buff=0.3)
        hdr = T("stack of pending runs", 18, C_DIM).move_to([-4.3, 1.45, 0])
        self.say("Now the rule. When the sort finds a run, it first computes the power of the run before it.",
                 2.6, anims=[FadeIn(rule), FadeIn(hdr), FadeIn(cost_l), FadeIn(cost_v)])

        SX, SY, DY = -4.6, -2.3, 0.68
        cur = None
        slots = []  # [box, power chip or None]
        cost = 0
        note = None

        def slot_box(n, i):
            return box(str(n), C_RUN, w=2.0, h=0.5, size=22).move_to([SX, SY + DY * i, 0])

        def pchip(p, i):
            return chip(f"power {p}", C_POW, 18, mono=False).move_to([SX + 1.9, SY + DY * i, 0])

        def set_note(text):
            nonlocal note
            new = T(text, 20, C_POW).move_to([2.6, -0.65, 0])
            anims = [FadeIn(new)]
            if note is not None:
                anims.append(FadeOut(note))
            note = new
            return anims

        def cursor_to(j):
            nonlocal cur
            r = SurroundingRectangle(top[j], buff=0.06, color=C_WARN, stroke_width=3)
            anims = [Create(r)] if cur is None else [ReplacementTransform(cur, r)]
            cur = r
            return anims

        def push(n):
            i = len(slots)
            b = slot_box(n, i)
            slots.append([b, None, n])
            return [FadeIn(b, shift=0.3 * DOWN)]

        def set_power(p):
            i = len(slots) - 1
            c = pchip(p, i)
            slots[i][1] = c
            return [FadeIn(c)]

        def merge(i):
            nonlocal cost
            (a, ac, na), (b, bc, nb) = slots[i], slots[i + 1]
            cost += na + nb
            nbx = slot_box(na + nb, i)
            gone = [m for m in (ac, bc) if m is not None]
            anims = [FadeTransform(VGroup(a, b), nbx), *[FadeOut(m) for m in gone]]
            rest = slots[i + 2:]
            for k, (bx, ch, _) in enumerate(rest):
                anims.append(bx.animate.move_to([SX, SY + DY * (i + 1 + k), 0]))
                if ch is not None:
                    anims.append(ch.animate.move_to([SX + 1.9, SY + DY * (i + 1 + k), 0]))
            slots[i:i + 2] = [[nbx, None, na + nb]]
            newv = M(str(cost), 24, C_COST).move_to(cost_v, aligned_edge=LEFT)
            anims.append(Transform(cost_v, newv))
            return anims

        ev = iter(TRACE)
        # Walk the trace run by run, with one caption per run.
        caps = {
            0: "The first run, 4, simply goes on the stack.",
            1: "6 arrives: the 4 gets power 3. Nothing is below it, so 6 is pushed.",
            2: "2 arrives: the 6 gets power 2. The 4 below has power 3, deeper, so 4 and 6 merge.",
            3: "5 arrives: the 2 gets power 3. The 10 below has power 2, so nothing merges yet.",
            4: "9 arrives: the 5 gets power 1, the root. Everything deeper below it merges: 2 + 5, then 10 + 7.",
            5: "3 arrives: the 9 gets power 2, deeper than the 1 below it, so nothing merges.",
            6: "The last 3 arrives, and the run before it gets power 3. Powers rise toward the top.",
        }
        notes = {1: "power(4 | 6) = 3", 2: "power(6 | 2) = 2", 3: "power(2 | 5) = 3", 4: "power(5 | 9) = 1",
                 5: "power(9 | 3) = 2", 6: "power(3 | 3) = 3"}
        e = next(ev)
        for j, n in enumerate(RUNS):
            step = cursor_to(j)
            if j == 0:
                assert e == ("push", n)
                self.say(caps[j], 1.8, anims=step + push(n))
                e = next(ev)
                continue
            assert e[0] == "power" and e[2] == POWERS[j - 1]
            p = e[2]
            first = step + set_note(notes[j])
            e = next(ev)
            merges = []
            while e[0] == "merge":
                merges.append(e)
                e = next(ev)
            assert e == ("push", n)
            if not merges:
                self.say(caps[j], 2.4, anims=first + set_power(p))
                self.play(*push(n), run_time=0.6)
            else:
                self.say(caps[j], 2.6, anims=first)
                for m in merges:
                    assert slots[m[1]][2] == m[2]
                    self.play(*merge(m[1]), run_time=0.8)
                self.play(*set_power(p), run_time=0.5)
                self.play(*push(n), run_time=0.6)
            e = next(ev, None)
        self.play(FadeOut(cur), *([FadeOut(note)] if note else []), run_time=0.4)
        note = None
        rest = [e] + list(ev)
        self.say("At the end, the runs left on the stack merge from the top: 3 + 3, then 9 + 6, then 17 + 15.",
                 2.2)
        for m in rest:
            assert m[0] == "merge"
            self.play(*merge(m[1]), run_time=0.8)
        assert cost == COST
        cmp = T(f"the old rule, same runs: {OLD_COST}", 20, C_OLD).next_to(cost_l, UP, buff=0.3).align_to(cost_l,
                                                                                                         LEFT)
        self.say(f"Total merge cost: {COST}. The old rule, on the same runs, costs {OLD_COST}.", 2.2,
                 anims=[FadeIn(cmp)])
        bound = VGroup(T("powers only rise toward the top, so the stack", 20),
                       T("holds at most log2(n) + 1 runs", 20),
                       M("MAX_MERGE_PENDING: 85, now bits in a size_t", 18, C_POW)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([2.6, -0.85, 0])
        self.say("Powers only rise toward the top, so the stack holds at most log2(n) + 1 runs.", 2.4,
                 anims=[FadeIn(bound[0]), FadeIn(bound[1])])
        self.say("Its fixed size drops from 85 slots to the bits in a size_t: 64 on a 64-bit build.", 2.4,
                 anims=[FadeIn(bound[2])])
        self.clear_all()


# ----------------------------------------------------------------------------
class S06Cases(Captioned):
    def construct(self):
        self.add(badge(6, "better, and sometimes worse"))
        W = 7.0  # width of a whole list
        X0 = -6.3

        def runs_row(lengths, labels, y, tiny_label):
            tot = sum(lengths)
            g, x, tiny = VGroup(), X0, []
            for i, n in enumerate(lengths):
                w = max(0.14, W * n / tot)
                c = C_RUN if i % 2 == 0 else C_RUN2
                r = Rectangle(width=w - 0.04, height=0.42, color=c, fill_color=c, fill_opacity=0.35, stroke_width=2)
                r.move_to([x + w / 2, y, 0])
                x += w
                g.add(r)
                if labels[i]:
                    g.add(T(labels[i], 18).move_to(r))
                else:
                    tiny.append(r)
            tl = T(tiny_label, 16, C_DIM).next_to(VGroup(*tiny), UP, buff=0.12)
            g.add(tl)
            return g

        def cost_bars(old, new, y):
            scale = 3.3 / 250_000_001
            out = VGroup()
            for k, (name, v, c) in enumerate([("old rule", old, C_OLD), ("powersort", new, C_NEW)]):
                yy = y - 0.45 * k
                lab = T(name, 18, c).move_to([1.9, yy, 0]).align_to([1.5, 0, 0], LEFT)
                bar = Rectangle(width=v * scale, height=0.26, color=c, fill_color=c, fill_opacity=0.5,
                                stroke_width=1.5).move_to([0, yy, 0]).align_to([2.85, 0, 0], LEFT)
                val = T(f"{v / 1e6:.0f}M", 18, c).next_to(bar, RIGHT, buff=0.12)
                out.add(VGroup(lab, bar, val))
            return out

        h1 = T("bad for the old rule", 22, C_OLD).move_to([0, 2.45, 0]).align_to([X0, 0, 0], LEFT)
        r1 = runs_row([50_000_000, 49_999_936, 64, 1], ["N/2", "N/2 - 64", None, None], 1.55, "64 and 1")
        c1 = cost_bars(250_000_001, 150_000_067, 1.75)
        h2 = T("bad for powersort", 22, C_NEW).move_to([0, 0.35, 0]).align_to([X0, 0, 0], LEFT)
        b = 100_000_000 // 128
        r2 = runs_row([(b - 1) * 64, 64, 64, b * 64], ["N/2 - 64", None, None, "N/2"], -0.55, "64 and 64")
        c2 = cost_bars(150_000_256, 200_000_128, -0.35)
        foot = T("merge cost with N = 100 million, computed with the PR's own C functions; both lists are "
                 "from the PR's comments", 16, C_DIM).move_to([0, -1.6, 0])
        fit(foot, 13)
        self.say("The PR's comments build a list the old rule handles badly: N/2, N/2 - 64, 64 and 1.", 2.4,
                 anims=[FadeIn(h1), FadeIn(r1)])
        self.say("With N = 100 million, the old rule's merge cost is 250 million; powersort's is 150 million.",
                 2.6, anims=[LaggedStart(FadeIn(c1[0]), FadeIn(c1[1]), lag_ratio=0.3), FadeIn(foot)])
        self.say("They also build the reverse: here powersort is the worse one, 200 million against 150.", 2.6,
                 anims=[FadeIn(h2), FadeIn(r2), LaggedStart(FadeIn(c2[0]), FadeIn(c2[1]), lag_ratio=0.3)])
        self.say("The author notes that powersort's bad cases are less bad than the old rule's.", 2.2)
        self.play(FadeOut(VGroup(h1, r1, c1, h2, r2, c2, foot)), run_time=0.6)

        pts = VGroup(
            T("every fast rule has bad cases: the optimal order takes time quadratic in the runs", 21),
            T("for any three runs powersort is optimal: it merges the shorter of A and C with B", 21),
            T("on ordinary lists, timings barely move (the author ran Lib/test/sortperf.py)", 21),
            T("what it buys: provable bounds, and a published paper with the proofs", 21, C_NEW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.42).move_to([0, 0.6, 0])
        for p in pts:
            fit(p, 13)
        caps = [
            "Every fast rule has bad cases. The truly optimal order takes time quadratic in the number of runs.",
            "For any three runs, powersort is always optimal: it merges the shorter of A and C with B.",
            "On ordinary lists, the author can barely detect a timing difference, running sortperf.py.",
            "The gain is a rule with provable bounds, and a published paper to read for the proofs.",
        ]
        for p, c in zip(pts, caps):
            self.say(c, 2.4, anims=[FadeIn(p, shift=0.1 * RIGHT)])
        self.clear_all()


# ----------------------------------------------------------------------------
class S07Review(Captioned):
    def construct(self):
        self.add(badge(7, "how to review it"))

        def section(title, color, items, mono=True, size=18):
            hd = T(title, 22, color)
            body = VGroup(*[(M if mono else T)(x, size, WHITE if mono else GREY_A) for x in items])
            body.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            return VGroup(hd, body).arrange(DOWN, aligned_edge=LEFT, buff=0.16)

        read = section("read first: Objects/listsort.txt", C_POW,
                       ["the merge-order section, about 100 lines,", "rewritten to explain powers"], mono=False)
        items = [("powerloop()", "the power, bit by bit"), ("found_new_run()", "replaces merge_collapse()"),
                 ("merge_init()", "keeps listlen and basekeys"), ("MAX_MERGE_PENDING", "85 slots, now 64")]
        rows = VGroup(*[VGroup(M(a, 17), T(b, 17, GREY_A)) for a, b in items])
        for r in rows:
            r[1].next_to(r[0], RIGHT, buff=0.3)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        for r in rows:
            r[1].align_to(rows[0][0], LEFT).shift(RIGHT * 3.0)
        code_s = VGroup(T("then Objects/listobject.c", 22, C_POW), rows).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        left = VGroup(read, code_s).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([-3.0, 0.55, 0])
        care = section("read carefully", C_OLD, ["the call site: the rule now runs", "before the new run is pushed"],
                       mono=False)
        tested = section("where it is tested", C_NEW, ["no new tests: the C was checked by hand",
                                                       "against runstack.py on bpo-34561"], mono=False)
        same = section("unchanged", C_DIM, ["merge_force_collapse(): the final", "merges still choose by length"],
                       mono=False)
        right = VGroup(care, tested, same).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([3.9, 0.55, 0])
        right.align_to(left, UP)
        self.say("Start with listsort.txt: its merge-order section now explains powers, in about 100 lines.", 2.4,
                 anims=[FadeIn(read)])
        self.say("Then listobject.c: powerloop() computes the power, and found_new_run() replaces "
                 "merge_collapse().", 2.6, anims=[FadeIn(code_s)])
        self.say("The call site moves: the rule now runs before the new run is pushed, not after.", 2.4,
                 anims=[FadeIn(care)])
        self.say("No tests are added. The author checked the C by hand against runstack.py, from the issue.", 2.6,
                 anims=[FadeIn(tested)])
        self.say("Note that the final merges, in merge_force_collapse(), still choose by run length.", 2.4,
                 anims=[FadeIn(same)])
        size = T("+178 -92 lines:  listsort.txt +98 -59  ·  listobject.c +79 -33  ·  NEWS +1", 20,
                 C_DIM).move_to(DOWN * 2.45)
        self.say("Most of the changed lines, 157 of 270, are the explanation in listsort.txt.", 2.2,
                 anims=[FadeIn(size)])
        self.clear_all()

        end = VGroup(T("a run's power: its depth in an ideal merge tree", 34),
                     T("merge while the run below is deeper", 34),
                     T("a stack of at most log2(n) + 1 runs", 34, C_POW)).arrange(DOWN, buff=0.4)
        self.play(LaggedStart(*[FadeIn(m, shift=0.1 * UP) for m in end], lag_ratio=0.3))
        self.wait(3)
        self.play(FadeOut(end))
