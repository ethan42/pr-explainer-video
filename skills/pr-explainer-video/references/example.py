"""Worked example: a complete 13-scene explainer for a fictional 46-file PR (a nightly smoke-test suite for CI).

The PR, its project and its numbers are made up for this example. Read it for density, pacing and
patterns, not for its subject. Patterns worth copying:
- S01: before/after split screen, the problem and the change side by side.
- S03: a chain of new names introduced one per caption, with a legend for what the colors mean.
- S04: what a cache key contains, what it does not, and events that do or do not re-key it.
- S05: a sorted queue, its stop rules as a table, and where the big data stays.
- S06: a worked algorithm on tiny data, driven step by step by a copy of the PR's own code (lazy_trace).
- S07/S10: decision tables revealed one row per caption.
- S12: how to review: what to read first, commit groups, files that need care, where the tests live.
"""

import heapq

from pr3b1b import *

# One meaning per color, for the whole video.
C_RAW = GREY_B     # raw inputs: code, history, lockfile
C_CHEAP = TEAL_C   # derived without running a test
C_MEAS = ORANGE    # measured by running tests
C_GEN = PURPLE_B   # the nightly publisher
C_RUN = BLUE_C     # CI infrastructure: runners, jobs, artifact storage
C_OUT = YELLOW_C   # the published file
C_GOLD = GOLD_C    # the reference runner
C_BRANCH = MAROON_B  # code branches a test reaches


def run_sq(kind):
    color = {"P": C_OK, "F": C_BAD, "T": C_WARN, "E": GREY_C}[kind]
    s = Square(0.42, color=color, fill_color=color, fill_opacity=0.35, stroke_width=2)
    return VGroup(s, M(kind, 20, WHITE).move_to(s))


# ----------------------------------------------------------------------------
class S00Intro(Captioned):
    def construct(self):
        title = T("The nightly smoke suite", 60, weight=BOLD)
        sub = T("PR #214, a fictional PR: picks the pull-request tests once a night", 26, C_DIM)
        head = VGroup(title, sub).arrange(DOWN, buff=0.3)
        self.play(Write(title), run_time=1.4)
        self.play(FadeIn(sub, shift=0.2 * UP))
        self.wait(1.2)
        self.play(head.animate.scale(0.6).to_edge(UP, buff=0.3))

        base = box2("test-history series", "#209–#213 · base branch ci/history", GREY_C, w=4.6, h=1.3,
                    size=24, sub=18, fill=0.12)
        top = box("#214  the smoke suite", C_OUT, w=4.6, h=0.7, size=24, fill=0.3)
        stack = VGroup(base, top).arrange(UP, buff=0.12).move_to(LEFT * 3.3 + DOWN * 0.3)
        self.play(FadeIn(base, shift=0.2 * UP))
        self.say("This PR sits on top of the test-history series, #209 to #213.", 1.8)
        self.play(FadeIn(top, shift=0.3 * DOWN))

        stats = lines(["12 commits", "+4,210 / −380 lines", "46 files",
                       "3 new decision records"], 26).move_to(RIGHT * 3.3 + DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(s, shift=0.1 * LEFT) for s in stats], lag_ratio=0.2), run_time=1.4)
        self.say("It moves test selection out of the pull-request job and into a nightly job on main.", 2.2)
        self.say("This video shows the end picture of the PR, not the history of its review.", 2.2)
        self.clear_all()


# ----------------------------------------------------------------------------
class S01Before(Captioned):
    def construct(self):
        self.add(badge(1, "where the tests are picked"))
        div = DashedLine(UP * 2.95, DOWN * 2.7, color=GREY_D)
        lh = T("before: in every pull-request job", 24, C_BAD).move_to([-3.6, 2.75, 0])
        rh = T("after: once a night, on main", 24, C_OK).move_to([3.6, 2.75, 0])
        self.play(Create(div), FadeIn(lh))

        img = box("test suite on main", C_RAW, w=2.8, h=0.6, size=22).move_to([-3.6, 1.8, 0])
        xs = [-5.5, -3.6, -1.7]
        jobs = VGroup(*[box(f"PR job {i + 1}", GREY_B, w=1.6, h=0.5, size=19, fill=0.12).move_to([x, 0.55, 0])
                        for i, x in enumerate(xs)])
        picks = VGroup(*[chip("sample", C_MEAS, 17).next_to(r, DOWN, buff=0.15) for r in jobs])
        hs = [[0.9, 0.6, 0.8, 0.4, 0.7], [0.7, 0.6, 0.5, 0.4, 0.9], [0.9, 0.3, 0.8, 0.6, 0.5]]
        bs = VGroup(*[bars(h, C_MEAS).next_to(e, DOWN, buff=0.2) for h, e in zip(hs, picks)])
        arrs = VGroup(*[arrow(img.get_bottom(), r.get_top()) for r in jobs])
        self.play(FadeIn(img), LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(r) for r in jobs], lag_ratio=0.2))
        self.say("Until now, every pull-request job picked its own tests, with a random sample.", 2.2)
        self.play(LaggedStart(*[FadeIn(e) for e in picks], lag_ratio=0.2))
        self.say("It sampled 300 of the package's 4,800 tests, ran them on main to learn which pass, then on the PR.", 2.4)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bs], lag_ratio=0.2))
        neq = T("three jobs, three different samples", 22, C_BAD).next_to(bs, DOWN, buff=0.3)
        self.play(FadeIn(neq))
        self.say("Two jobs could test two different samples, and every one paid for the run on main.", 2.6)

        self.play(FadeIn(rh))
        gen = box("nightly job, on main", C_GEN, w=4.4, h=0.55, size=20).move_to([3.6, 1.95, 0])
        art = RoundedRectangle(corner_radius=0.1, width=3.4, height=1.0, color=C_RUN, fill_color=C_RUN,
                               fill_opacity=0.2, stroke_width=2.5).move_to([3.6, 0.75, 0])
        art_t = T("CI artifacts", 20).move_to(art.get_top() + DOWN * 0.25)
        sj = chip("smoke.json", C_OUT, 18).move_to(art.get_bottom() + UP * 0.32)
        a0 = arrow(gen.get_bottom(), art.get_top())
        self.play(FadeIn(gen), GrowArrow(a0), FadeIn(art), FadeIn(art_t))
        self.say("Now the tests are picked once a night, on main, and published as one file.", 2.2,
                 anims=[FadeIn(sj, scale=1.3)])
        xs2 = [1.8, 3.6, 5.4]
        jobs2 = VGroup(*[box(f"PR job {i + 1}", GREY_B, w=1.6, h=0.5, size=19, fill=0.12).move_to([x, -0.55, 0])
                         for i, x in enumerate(xs2)])
        arrs2 = VGroup(*[arrow(art.get_bottom(), r.get_top()) for r in jobs2])
        same = [0.9, 0.6, 0.8, 0.4, 0.7]
        bs2 = VGroup(*[bars(same, C_OUT).next_to(r, DOWN, buff=0.3) for r in jobs2])
        eq = T("one shared smoke suite", 22, C_OK).next_to(bs2, DOWN, buff=0.3)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrs2], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(r) for r in jobs2], lag_ratio=0.2))
        self.play(LaggedStart(*[TransformFromCopy(sj, b) for b in bs2], lag_ratio=0.2), run_time=1.4)
        self.play(FadeIn(eq))
        self.say("Every pull-request job downloads smoke.json and runs exactly those tests on the PR.", 2.6)
        self.say("The merge queue still runs the full suite, as before.", 2.0)
        self.clear_all()


# ----------------------------------------------------------------------------
class S02Suite(Captioned):
    def construct(self):
        self.add(badge(2, "the picture: one suite"))
        top = box("suite: one package's tests on one main commit", C_OUT, w=6.4, h=0.65, size=24).move_to(UP * 2.3)
        tl = M("SuiteKey", 18, C_OUT).next_to(top, RIGHT, buff=0.2)
        self.play(FadeIn(top, shift=0.2 * DOWN), FadeIn(tl))
        self.say("A suite is what we pick tests from: one package's tests, on one commit of main.", 2.2)

        names = ["linux-x64", "linux-arm64", "macos-arm64"]
        runners = VGroup(*[box2(n, "image + toolchain digests", C_RUN, w=3.0, h=0.8, size=22,
                                sub=15).move_to([x, 0.7, 0]) for n, x in zip(names, [-4.2, 0.0, 4.2])])
        rl0 = VGroup(*[Line(b.get_top(), top.get_bottom(), color=GREY_C, stroke_width=2) for b in runners])
        self.play(LaggedStart(*[FadeIn(b, shift=0.2 * UP) for b in runners], lag_ratio=0.2), Create(rl0))
        self.say("It runs on one runner for each platform that CI supports.", 1.8)

        rx = [(-5.0, 0), (-3.4, 0), (0.0, 1), (4.2, 2)]
        runs = VGroup(*[chip(f"run {i + 1}", GREY_A, 20).move_to([x, -0.9, 0]) for i, (x, _) in enumerate(rx)])
        rl = VGroup(*[Line(runs[i].get_top(), runners[b].get_bottom(), color=GREY_C, stroke_width=2)
                      for i, (_, b) in enumerate(rx)])
        self.play(LaggedStart(*[FadeIn(r) for r in runs], lag_ratio=0.15), Create(rl))
        self.say("Each nightly run used one of those runners and left a test history behind.", 1.8)

        ent = T("HISTORY: which runs count for the suite, and why", 22, C_RAW).move_to(DOWN * 2.15)
        self.play(FadeIn(ent))
        ok = VGroup(*[T("✓", 26, C_OK).next_to(runs[i], RIGHT, buff=0.1) for i in (0, 1, 3)])
        no = T("✗", 26, C_BAD).next_to(runs[2], RIGHT, buff=0.1)
        why = T("cancelled: left out", 18, C_BAD).next_to(runs[2], DOWN, buff=0.15)
        self.play(FadeIn(ok), FadeIn(no), FadeIn(why), runs[2].animate.fade(0.6))
        self.say("The suite's history counts some runs, and leaves others out with a reason, such as a cancel.",
                 2.0)

        new_t = fit(VGroup(T("reference runner", 22, C_GOLD), T("linux-x64 · 4 CPU · 8 GiB", 16, GREY_A)).arrange(
            DOWN, buff=0.08), 2.8).move_to(runners[0][0])
        self.play(runners[0][0].animate.set_stroke(C_GOLD, 4), FadeTransform(runners[0][1], new_t),
                  runners[1].animate.fade(0.65), runners[2].animate.fade(0.65))
        self.say("The CI config names one reference runner. Every measurement runs there, and nowhere else.", 2.6)
        self.say("So the smoke suite depends on the suite and on that one runner, not on the others.", 2.0)
        self.clear_all()


# ----------------------------------------------------------------------------
FACTS = [
    ("TEST_LIST", C_CHEAP, "cheap · the collected test ids and the digest of the code"),
    ("COVERAGE", C_MEAS, "measured · one coverage run · the branches each test reaches"),
    ("ORDER", C_CHEAP, "cheap · a greedy order, computed from COVERAGE"),
    ("STABILITY", C_MEAS, "measured · one stability run · 3 runs per test, first 100 stable"),
    ("SMOKE", C_CHEAP, "cheap · the first 100 stable tests of ORDER"),
]


class S03Facts(Captioned):
    def construct(self):
        self.add(badge(3, "five new names"))
        raw = VGroup(*[chip(n, C_RAW, 17) for n in ["CODE", "HISTORY", "LOCKFILE"]])
        raw.arrange(RIGHT, buff=0.18).move_to([-3.2, 2.75, 0])
        leg = VGroup(
            VGroup(Square(0.25, color=C_CHEAP, fill_opacity=0.4), T("cheap: runs no test", 18)).arrange(RIGHT,
                                                                                                    buff=0.15),
            VGroup(Square(0.25, color=C_MEAS, fill_opacity=0.4),
                   T("measured: runs tests on the reference runner", 18)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([3.6, 2.7, 0])
        self.play(FadeIn(raw))
        self.say("The raw inputs are the package's code, the suite's history and the lockfile.", 2.2)

        ys = [1.7, 0.7, -0.3, -1.3, -2.3]
        boxes = VGroup(*[box(n, c, w=3.4, h=0.55, size=20, mono=True).move_to([-3.2, y, 0])
                         for (n, c, _), y in zip(FACTS, ys)])
        descs = VGroup(*[fit(T(d, 19, GREY_A), 7.6).next_to(b, RIGHT, buff=0.45) for (_, _, d), b in
                         zip(FACTS, boxes)])
        a_raw = arrow(raw.get_bottom(), boxes[0].get_top())
        chain = VGroup(*[arrow(boxes[i].get_bottom(), boxes[i + 1].get_top()) for i in range(4)])
        self.play(FadeIn(leg))
        steps = [
            "TEST_LIST is cheap: collect the tests without running them, and hash the package's code.",
            "COVERAGE is measured: one coverage run records the branches each test reaches.",
            "ORDER is cheap: it sorts the tests by the coverage they add, from COVERAGE alone.",
            "STABILITY is measured: it runs the tests in ORDER, 3 times each, and keeps the first 100 stable.",
            "SMOKE is cheap: the stable tests, in ORDER's order. It is what PR jobs run.",
        ]
        for i in range(5):
            anims = [FadeIn(boxes[i], shift=0.15 * DOWN), FadeIn(descs[i])]
            anims.append(GrowArrow(a_raw) if i == 0 else GrowArrow(chain[i - 1]))
            self.play(*anims, run_time=0.8)
            self.say(steps[i], 2.0)

        self.play(FadeOut(descs), FadeOut(leg))
        gen = box("publisher", C_GEN, w=2.8, h=0.65, size=22).move_to([1.6, -0.3, 0])
        out = chip("smoke.json", C_OUT, 20).move_to([4.6, -0.3, 0])
        ins = VGroup(*[arrow(b.get_right(), gen.get_left(), color=GREY_C, sw=2) for b in boxes])
        self.play(FadeIn(gen), LaggedStart(*[GrowArrow(a) for a in ins], lag_ratio=0.1))
        a_out = arrow(gen.get_right(), out.get_left(), color=C_OUT)
        self.play(GrowArrow(a_out), FadeIn(out, scale=1.2))
        readers = fit(VGroup(T("read by PR jobs, local runs", 19, GREY_A), T("and the flaky-test report", 19, GREY_A)
                             ).arrange(DOWN, buff=0.08), 3.6).next_to(out, DOWN, buff=0.3)
        self.play(FadeIn(readers))
        self.say("The publisher picks one stability result and writes it out as smoke.json.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
class S04Keys(Captioned):
    def construct(self):
        self.add(badge(4, "what the expensive runs are keyed on"))
        cl = M("COVERAGE  key", 20, C_MEAS).move_to([-3.6, 2.45, 0])
        ck1 = VGroup(chip("TEST_LIST b41e…", C_CHEAP, 17), chip("LOCKFILE 81c0…", C_RAW, 17)).arrange(
            RIGHT, buff=0.15)
        ck2 = VGroup(chip("runner 4 CPU · 8 GiB", GREY_A, 17))
        ck = VGroup(ck1, ck2).arrange(DOWN, buff=0.15).next_to(cl, DOWN, buff=0.2)
        sl = M("STABILITY  key", 20, C_MEAS).move_to([-3.6, 0.75, 0])
        sk1 = VGroup(chip("ORDER 9d02…", C_CHEAP, 17), chip("runner 4 CPU · 8 GiB", GREY_A, 17)).arrange(
            RIGHT, buff=0.15)
        sk2 = VGroup(chip("runs 3", GREY_A, 17), chip("wanted 100", GREY_A, 17)).arrange(RIGHT, buff=0.15)
        sk = VGroup(sk1, sk2).arrange(DOWN, buff=0.15).next_to(sl, DOWN, buff=0.2)
        self.play(FadeIn(cl), FadeIn(ck))
        self.say("The coverage run is keyed on TEST_LIST, the lockfile and the runner's size.", 2.2)
        self.play(FadeIn(sl), FadeIn(sk))
        self.say("The stability run is keyed on ORDER's value, the runner, and how many runs and tests.", 2.2)

        nh = T("in no key", 24, C_BAD).move_to([3.7, 2.45, 0])
        items = lines(["the commit message and its author", "the time of night the job runs",
                       "docs and other files that are not code", "where the artifacts are stored",
                       "the deadline", "the other runners"], 19, GREY_A, buff=0.2)
        nh.align_to([0.8, 0, 0], LEFT)
        items.next_to(nh, DOWN, buff=0.3).align_to(nh, LEFT)
        strikes = VGroup(*[strike(i) for i in items])
        self.play(FadeIn(nh), LaggedStart(*[FadeIn(i) for i in items], lag_ratio=0.1))
        self.play(LaggedStart(*[Create(s) for s in strikes], lag_ratio=0.1))
        self.say("Nothing else enters: not the commit, not the docs, not storage, not the deadline.", 2.4)

        ev = chip("a docs-only commit lands", GREY_A, 18, mono=False).move_to([-4.6, -1.75, 0])
        tl = chip("TEST_LIST b41e…", C_CHEAP, 18).move_to([-0.6, -1.75, 0])
        res = T("same value: no new run", 22, C_OK).move_to([3.6, -1.75, 0])
        a1 = arrow(ev.get_right(), tl.get_left())
        a2 = arrow(tl.get_right(), res.get_left())
        self.play(FadeIn(ev), GrowArrow(a1))
        self.play(FadeIn(tl))
        self.play(Indicate(tl, color=C_OK))
        self.play(GrowArrow(a2), FadeIn(res))
        self.say("Main can move without moving what is measured: then TEST_LIST keeps its value.", 2.6)
        self.play(FadeOut(VGroup(ev, tl, res, a1, a2)))

        ev2 = chip("a test file changes", GREY_A, 18, mono=False).move_to([-4.6, -1.75, 0])
        old = ck1[0]
        new = chip("TEST_LIST 7c21…", C_CHEAP, 17).move_to(old)
        res2 = T("coverage re-runs; stability only if ORDER changes", 22, C_WARN).move_to([2.3, -1.75, 0])
        a3 = arrow(ev2.get_right(), res2.get_left())
        self.play(FadeIn(ev2))
        self.play(Transform(old, new), Flash(old, color=C_WARN))
        self.play(GrowArrow(a3), FadeIn(res2))
        self.say("A changed test file re-keys the coverage run. Stability re-runs only if ORDER changes.", 2.6)
        ev3 = chip("the deadline is raised", GREY_A, 18, mono=False).align_to(ev2, RIGHT).set_y(-1.75)
        res3 = T("in no key: nothing re-measured", 22, C_OK).next_to(a3.get_end(), RIGHT, buff=0.12)
        self.play(FadeTransform(ev2, ev3), FadeTransform(res2, res3))
        self.say("A change to anything outside the keys re-measures nothing.", 2.2)
        self.clear_all()


# ----------------------------------------------------------------------------
class S05Coverage(Captioned):
    def construct(self):
        self.add(badge(5, "the coverage run"))
        times = ["0.8 s", "—", "0.1 s", "2.4 s", "0.3 s", "—", "0.1 s", "1.2 s"]

        def secs(t):
            return float(t.split()[0])

        fastest = sorted([t for t in times if t != "—"], key=secs) + ["—", "—"]

        def cell(t):
            s = Square(0.55, color=C_RAW, fill_color=C_RAW, fill_opacity=0.2, stroke_width=2)
            return VGroup(s, T(t, 14, GREY_A).next_to(s, DOWN, buff=0.08))

        cells = VGroup(*[cell(t) for t in times]).arrange(RIGHT, buff=0.3, aligned_edge=UP).move_to(UP * 1.9)
        cl = T("candidates: the tests that passed in every counted run", 22).next_to(cells, UP, buff=0.3)
        self.play(FadeIn(cl), LaggedStart(*[FadeIn(c) for c in cells], lag_ratio=0.08))
        self.say("The candidates are the tests that passed in every run the history counts.", 2.0)
        slots = [c[0].get_center() for c in cells]
        used = set()
        moves = []
        for target, t in enumerate(fastest):
            src = next(i for i, x in enumerate(times) if x == t and i not in used)
            used.add(src)
            moves.append(cells[src].animate.shift(slots[target] - cells[src][0].get_center()))
        self.play(*moves, run_time=1.4)
        nl = T("fastest first · test id breaks ties · never timed last", 20, C_WARN).next_to(cells, DOWN, buff=0.2)
        self.play(FadeIn(nl))
        self.say("The job lays them out fastest first, so that ties in coverage go to the cheaper test.", 2.4)

        ctr = RoundedRectangle(corner_radius=0.15, width=11.5, height=2.5, color=C_MEAS, stroke_width=2.5).move_to(
            DOWN * 0.9)
        ctl = T("coverage job · reference runner · pytest --cov --cov-context=test", 19, C_MEAS).next_to(
            ctr.get_top(), DOWN, buff=0.15)
        lanes = VGroup(*[Line([-4.2, y, 0], [5.3, y, 0], color=GREY_D, stroke_width=2) for y in
                         (-0.5, -1.0, -1.5, -2.0)])
        lane_l = VGroup(*[T(f"shard {i + 1}", 16, C_DIM).move_to([-4.9, y, 0]) for i, y in
                          enumerate((-0.5, -1.0, -1.5, -2.0))])
        self.play(Create(ctr), FadeIn(ctl), Create(lanes), FadeIn(lane_l))
        sorted_cells = sorted(cells, key=lambda c: c.get_center()[0])
        dots = [c[0].copy() for c in sorted_cells]
        self.play(LaggedStart(*[d.animate.scale(0.6).move_to([-3.6 + 1.0 * (k // 4), (-0.5, -1.0, -1.5, -2.0)[k % 4], 0])
                                for k, d in enumerate(dots)], lag_ratio=0.08), run_time=1.6)
        self.say("Each test runs alone under coverage, dealt round-robin to 4 shards, one container each.", 2.2)
        self.say("The run keeps the longest prefix of the order in which every test finished.", 2.0)
        self.play(FadeOut(VGroup(*dots)), FadeOut(lanes), FadeOut(lane_l), FadeOut(cells), FadeOut(nl), FadeOut(cl),
                  FadeOut(ctr), FadeOut(ctl))

        rows = [
            ("probe the first 50 tests: ≥ 80% record no branches", "coverage-broken: stop", C_RAW),
            ("the package has no coverage configuration", "no-coverage: stop", C_RAW),
            ("complete · count cap of 10,000 · time cap", "a result, even if partial", C_OK),
            ("non-zero exit · container timeout · a shard crashes", "a failure, retried", C_BAD),
        ]
        tbl = VGroup()
        for i, (cond, res, col) in enumerate(rows):
            a = fit(T(cond, 21), 7.2)
            b = T(res, 21, col)
            a.move_to([-2.6, 2.0 - 0.8 * i, 0]).align_to([-6.4, 0, 0], LEFT)
            b.move_to([0, 2.0 - 0.8 * i, 0]).align_to([1.6, 0, 0], LEFT)
            tbl.add(VGroup(a, b))
        for r, cap in zip(tbl, [
            "A probe stops the run early when coverage is plainly broken, and says so.",
            "A package with no coverage set up has nothing to measure: a final answer, not a failure.",
            "A run that stops at its count cap or its deadline is still a valid result for its prefix.",
            "A run that gives no result is a failure. It is retried the next night, and never stored.",
        ]):
            self.play(FadeIn(r, shift=0.1 * RIGHT))
            self.say(cap, 2.2)
        self.play(FadeOut(tbl))

        inside = RoundedRectangle(corner_radius=0.15, width=6.0, height=2.6, color=C_MEAS, stroke_width=2.5).move_to(
            LEFT * 3.0 + DOWN * 0.2)
        il = T("coverage job", 20, C_MEAS).next_to(inside.get_top(), DOWN, buff=0.15)
        big = box2("per-test branch maps", "about 900 MB per suite", C_BAD, w=4.6, h=1.0, size=22, sub=18,
                   fill=0.25).move_to(inside).shift(DOWN * 0.2)
        small = box2("greedy order (test id, gain), statuses", "about 70 bytes per test", C_OK, w=5.2, h=1.0,
                     size=20, sub=18, fill=0.25).move_to(RIGHT * 3.6 + DOWN * 0.2)
        self.play(Create(inside), FadeIn(il), FadeIn(big))
        self.say("The per-test branch maps of one suite come to about 900 megabytes.", 2.0)
        out = arrow(inside.get_right(), small.get_left(), color=C_OK)
        self.play(GrowArrow(out), FadeIn(small))
        self.say("So the greedy order is computed inside the job. The branch maps never leave it.", 2.2)
        note = T("ci/coverage.py reads coverage.py's per-test contexts, on coverage.py 6 and 7", 19,
                 GREY_A).move_to(DOWN * 2.3)
        self.play(FadeIn(fit(note, 13)))
        self.say("A new module reads coverage.py's per-test contexts. It is tested on versions 6 and 7.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
G_ORDER = ["t1", "t2", "t3", "t4", "t5", "t6"]
G_BRANCHES = {"t1": {1, 2, 3}, "t2": {3, 4, 5, 6}, "t3": {1, 2, 3, 4, 5}, "t4": {6, 7}, "t5": {7, 8}, "t6": set()}


def lazy_trace(order, branches):
    """The steps of greedy.lazy_greedy_order over these tests: (kind, name, stale, fresh, next_name, next_bound)."""
    rank = {n: i for i, n in enumerate(order)}
    names = [n for n in order if branches[n]]
    union = frozenset().union(*[branches[n] for n in names])
    heap = [(-len(branches[n]), rank[n], n) for n in names]
    heapq.heapify(heap)
    covered = frozenset()
    steps = []
    while covered != union:
        neg, at, n = heapq.heappop(heap)
        fresh = (-len(branches[n] - covered), at, n)
        nxt = (heap[0][2], -heap[0][0]) if heap else (None, None)
        if heap and fresh > heap[0]:
            heapq.heappush(heap, fresh)
            steps.append(("push", n, -neg, -fresh[0], *nxt))
            continue
        covered |= branches[n]
        steps.append(("take", n, -neg, -fresh[0], *nxt))
    return steps


class S06Greedy(Captioned):
    def construct(self):
        bdg = badge(6, "the greedy order (ci/greedy.py)")
        self.add(bdg)
        rank = {n: i for i, n in enumerate(G_ORDER)}
        ry = {n: 2.0 - 0.55 * i for i, n in enumerate(G_ORDER)}
        cx = [-5.2 + 0.45 * j for j in range(8)]
        fh = T("branches", 18, C_DIM).move_to([(cx[0] + cx[-1]) / 2, 2.55, 0])
        nh = T("fastest ↓", 16, C_DIM).move_to([-6.25, 2.55, 0])
        labels = VGroup(*[M(n, 20).move_to([-6.25, ry[n], 0]) for n in G_ORDER])
        grid = {}
        for n in G_ORDER:
            for j in range(8):
                on = (j + 1) in G_BRANCHES[n]
                sq = Square(0.36, stroke_width=1.5, color=GREY_D if not on else C_BRANCH,
                            fill_color=C_BRANCH, fill_opacity=0.65 if on else 0.0).move_to([cx[j], ry[n], 0])
                grid[(n, j)] = sq
        cov_l = T("covered", 16, C_DIM).move_to([-6.25, -1.35, 0])
        cov = VGroup(*[Square(0.36, stroke_width=1.5, color=GREY_D).move_to([cx[j], -1.35, 0]) for j in range(8)])
        self.play(FadeIn(fh), FadeIn(nh), FadeIn(labels), FadeIn(VGroup(*grid.values())), FadeIn(cov_l),
                  FadeIn(cov))
        self.say("Six tests, fastest first, and the branches each one reaches.", 2.0)
        self.say("A cover keeps taking the test that adds the most uncovered branches. Ties go to the faster.",
                 2.6)

        hh = T("heap of stale bounds", 20, C_DIM).move_to([2.0, 2.55, 0])
        bound = {n: len(G_BRANCHES[n]) for n in G_ORDER if G_BRANCHES[n]}
        chips = {}
        for n in bound:
            r = RoundedRectangle(corner_radius=0.08, width=2.0, height=0.44, color=C_MEAS, fill_color=C_MEAS,
                                 fill_opacity=0.15, stroke_width=2)
            nm = M(n, 20).move_to(r.get_left() + RIGHT * 0.4)
            bd = M(str(bound[n]), 20, C_WARN).move_to(r.get_right() + LEFT * 0.4)
            chips[n] = VGroup(r, nm, bd)
        live = list(bound)

        def pos(k):
            return np.array([2.0, 2.0 - 0.55 * k, 0])

        def order_live():
            return sorted(live, key=lambda n: (-bound[n], rank[n]))

        for k, n in enumerate(order_live()):
            chips[n].move_to(pos(k))
        self.play(FadeIn(hh), LaggedStart(*[FadeIn(chips[n]) for n in order_live()], lag_ratio=0.1))
        self.say("Lazy greedy keeps each gain as last computed. Gains only shrink, so each is an upper bound.",
                 2.6)

        cover_l = T("first cover:", 20, C_OK).move_to([1.2, -1.35, 0])
        self.play(FadeIn(cover_l))
        covered = set()
        taken = []
        note = None
        caps = {
            0: "Pop t3: its fresh gain, 5, beats the next bound, 4. Take it.",
            1: "Pop t2: bound 4, but only 1 branch is still new, less than the next bound. Push it back.",
            2: "t1 adds nothing new now: push it back with 0.",
            3: "t4 adds 2, as many as t5's bound, and t4 is faster. Take it.",
            4: "t5 now adds 1, tied with t2's bound, and t2 is faster. Push t5 back.",
            5: "t2's true gain is 0 now. Push it back.",
            6: "t5 adds 1, more than any bound left. Take it: every branch is covered.",
        }
        for si, (kind, n, stale, fresh, nn, nb) in enumerate(lazy_trace(G_ORDER, G_BRANCHES)):
            c = chips[n]
            self.play(c[0].animate.set_stroke(C_WARN, 4), run_time=0.4)
            verdict = "take" if kind == "take" else "push back"
            nxt = f"next {nb} ({nn})" if nn else "heap empty"
            txt = T(f"fresh {fresh} vs {nxt}: {verdict}", 18, C_OK if kind == "take" else C_WARN)
            fit(txt, 3.4).next_to(c, RIGHT, buff=0.2)
            if note is None:
                self.play(FadeIn(txt), run_time=0.5)
            else:
                self.play(ReplacementTransform(note, txt), run_time=0.5)
            note = txt
            self.say(caps.get(si, ""), 1.6)
            if kind == "push":
                bound[n] = fresh
                newb = M(str(fresh), 20, C_WARN).move_to(c[2])
                self.play(Transform(c[2], newb), c[0].animate.set_stroke(C_MEAS, 2), run_time=0.5)
                self.play(*[chips[m].animate.move_to(pos(k)) for k, m in enumerate(order_live())],
                          note.animate.set_opacity(0), run_time=0.7)
            else:
                live.remove(n)
                newly = [j for j in range(8) if (j + 1) in G_BRANCHES[n] and (j + 1) not in covered]
                covered |= G_BRANCHES[n]
                slot = np.array([2.4 + 1.0 * len(taken), -1.35, 0])
                taken.append(n)
                small = chip(n, C_OK, 20)
                self.play(*[grid[(n, j)].animate.set_stroke(C_OK, 3) for j in range(8) if (j + 1) in G_BRANCHES[n]],
                          *[cov[j].animate.set_fill(C_OK, 0.7).set_stroke(C_OK) for j in newly],
                          ReplacementTransform(c, small.move_to(slot)), note.animate.set_opacity(0), run_time=0.8)
                if live:
                    self.play(*[chips[m].animate.move_to(pos(k)) for k, m in enumerate(order_live())], run_time=0.5)
        self.say("The first cover is t3, t4, t5: three tests reach every branch.", 2.0)
        self.say("It finds the same cover as recomputing every gain each step, with far fewer recomputations.",
                 2.4)

        self.play(*[FadeOut(m) for m in self.mobjects if m is not self.caption and m is not bdg], run_time=0.6)
        final = [("t3", 5), ("t4", 2), ("t5", 1), ("t2", 0), ("t1", 0), ("t6", 0)]
        row = VGroup(*[chip(f"{n}  +{g}", C_OK if g else GREY_A, 22) for n, g in final]).arrange(RIGHT, buff=0.45)
        row.move_to(UP * 1.2)
        b1 = Brace(row[0:3], DOWN)
        b2 = Brace(row[3:5], DOWN)
        b3 = Brace(row[5:6], DOWN)
        t1 = T("first cover: 3 tests", 18, C_OK).next_to(b1, DOWN)
        t2 = T("second cover", 18, GREY_A).next_to(b2, DOWN)
        t3 = T("no branches", 18, GREY_A).next_to(b3, DOWN)
        self.play(LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in row], lag_ratio=0.12))
        self.play(GrowFromCenter(b1), FadeIn(t1), GrowFromCenter(b2), FadeIn(t2), GrowFromCenter(b3), FadeIn(t3))
        self.say("Covers repeat over the tests left, so the order is total. Tests with no branches come last.", 2.4)
        self.say("Each test carries its gain over everything before it: positive exactly on the first cover.", 2.4)

        stats = VGroup(
            T("on this package's suite", 20, C_DIM),
            T("first cover: 310 of the 4,800 tests", 24),
            T("the first 100 of the greedy order reach 87% of the branches", 24, C_WARN),
        ).arrange(DOWN, buff=0.22).move_to(DOWN * 1.5)
        self.play(FadeIn(stats[0]), FadeIn(stats[1]))
        self.say("Even the first cover is too big: a PR job runs at most 100 tests in 3 minutes.", 2.2)
        self.play(FadeIn(stats[2]))
        self.say("So the smoke suite is the first 100 stable tests of this order (decision record 0007).", 2.2)
        self.say("Tests the coverage run did not reach follow, in name order.", 2.0)
        self.clear_all()


# ----------------------------------------------------------------------------
class S07Stability(Captioned):
    def construct(self):
        self.add(badge(7, "the stability rule (decision record 0008)"))
        hd = T("each test: 3 runs, in a fresh process each, on the 4 CPU · 8 GiB reference runner", 22).move_to(
            UP * 2.55)
        self.play(FadeIn(hd))
        self.say("A smoke test must give the same answer every time. Each test is run three times to check it.", 2.2)
        rows = [
            (["PPP"], "stable", "ships", C_OK),
            (["FFF", "TTT"], "broken on main", "the next test takes its place", GREY_A),
            (["PFP"], "flaky", "left out, and reported to its owners", C_BAD),
            (["EEE"], "runner error", "the stability run fails: retried tonight", C_WARN),
        ]
        caps = [
            "Three passes: the test is stable, and it ships.",
            "Three failures or three timeouts: the test is broken on main, and the next one replaces it.",
            "A pass beside a failure is flaky. It is left out, and the flaky-test report names it.",
            "Three runner errors may be the machine's fault, so the whole run fails and is retried.",
        ]
        table = VGroup()
        for i, (pats, verdict, effect, col) in enumerate(rows):
            y = 1.6 - 0.85 * i
            icons = VGroup()
            for p in pats:
                icons.add(VGroup(*[run_sq(k) for k in p]).arrange(RIGHT, buff=0.06))
            if len(icons) == 2:
                icons = VGroup(icons[0], T("or", 18, C_DIM), icons[1]).arrange(RIGHT, buff=0.15)
            icons.move_to([0, y, 0]).align_to([-6.6, 0, 0], LEFT)
            v = T(verdict, 22, col).move_to([0, y, 0]).align_to([-2.6, 0, 0], LEFT)
            e = fit(T(effect, 20, GREY_A), 6.0).move_to([0, y, 0]).align_to([0.2, 0, 0], LEFT)
            table.add(VGroup(icons, v, e))
        for r, cap in zip(table, caps):
            self.play(FadeIn(r, shift=0.1 * RIGHT), run_time=0.7)
            self.say(cap, 2.0)
        key = VGroup(*[VGroup(run_sq(k).scale(0.7), T(w, 16, C_DIM)).arrange(RIGHT, buff=0.08) for k, w in
                       [("P", "pass"), ("F", "fail"), ("T", "timeout"), ("E", "runner error")]]).arrange(RIGHT,
                                                                                                         buff=0.4)
        key.move_to(DOWN * 2.5)
        self.play(FadeIn(key))
        self.wait(1)
        self.play(FadeOut(table), FadeOut(key))

        of = VGroup(
            T("a test is also left out as too slow when one run", 21),
            T("takes more than 1 s, or", 21, C_WARN),
            T("needs more than 1 GiB of memory", 21, C_WARN),
        ).arrange(DOWN, buff=0.2).move_to(UP * 1.3)
        self.play(FadeIn(of))
        self.say("A PR job has 3 minutes for 100 tests, so a test that would not fit the budget does not ship.", 2.4)
        self.play(FadeOut(of))

        n = 9
        wanted = 6
        outcome = ["s", "s", "x", "s", "s", "x", "s", "x", "s"]
        q = VGroup(*[Square(0.5, color=C_RAW, fill_color=C_RAW, fill_opacity=0.2, stroke_width=2) for _ in range(n)])
        q.arrange(RIGHT, buff=0.18).move_to(UP * 1.0)
        ql = T("the greedy order", 20, C_DIM).next_to(q, UP, buff=0.2)
        sh = VGroup(*[Square(0.5, color=C_OK, stroke_width=2) for _ in range(wanted)]).arrange(RIGHT, buff=0.18)
        sh.move_to(DOWN * 1.0)
        sl = T("shipped (shown with 6 instead of 100)", 20, C_OK).next_to(sh, DOWN, buff=0.2)
        self.play(FadeIn(ql), FadeIn(q), FadeIn(sh), FadeIn(sl))
        self.say("The run takes the head of the order, and replaces each test that is left out by the next.", 2.0)
        i = 0
        got = 0
        while got < wanted and i < n:
            need = wanted - got
            window = list(range(i, min(n, i + need)))
            self.play(*[q[k].animate.set_stroke(C_WARN, 3) for k in window], run_time=0.4)
            anims = []
            for k in window:
                if outcome[k] == "s":
                    anims.append(q[k].animate.set_fill(C_OK, 0.6).set_stroke(C_OK).move_to(sh[got].get_center()))
                    got += 1
                else:
                    anims.append(q[k].animate.set_fill(GREY_D, 0.6).set_stroke(GREY_D))
            self.play(*anims, run_time=0.9)
            i = window[-1] + 1
        self.say("It stops when 100 tests are stable, or when the order runs out.", 2.0)
        self.clear_all()


# ----------------------------------------------------------------------------
class S08Run(Captioned):
    def construct(self):
        self.add(badge(8, "one stability run (ci/stability.py)"))
        job = RoundedRectangle(corner_radius=0.15, width=13.4, height=2.6, color=C_MEAS, stroke_width=2.5)
        job.move_to(UP * 0.9)
        fl = T("one container on the reference runner · --cpus 4 · --memory 8g · network off", 18,
               C_MEAS).next_to(job.get_top(), DOWN, buff=0.15)
        stages = [
            ("install", "once, from the lockfile"),
            ("runs", "3 each, until 100 stable"),
            ("timing", "the median of each test's runs"),
            ("coverage", "shipped list → branches_pre"),
        ]
        bs = VGroup(*[box2(a, b, C_MEAS, w=2.9, h=1.0, size=22, sub=15, fill=0.15) for a, b in stages])
        bs.arrange(RIGHT, buff=0.35).move_to(job).shift(DOWN * 0.15)
        arrs = VGroup(*[arrow(bs[i].get_right(), bs[i + 1].get_left(), buff=0.03) for i in range(3)])
        self.play(Create(job), FadeIn(fl))
        caps = [
            "It installs the dependencies once, from the lockfile, then turns the network off.",
            "It runs the order three times per test, each run in a fresh process.",
            "It keeps each test's median time, so the PR job can check its budget before it starts.",
            "Last, one coverage pass over the shipped list measures branches_pre.",
        ]
        for i in range(4):
            anims = [FadeIn(bs[i], shift=0.1 * RIGHT)]
            if i:
                anims.append(GrowArrow(arrs[i - 1]))
            self.play(*anims, run_time=0.7)
            self.say(caps[i], 2.2)
        self.say("A PR job measures branches_post the same way, over the same list.", 2.0)

        left = VGroup(T("a result, stored", 22, C_OK), M("completed", 19), M("flaky-found", 19)).arrange(
            DOWN, aligned_edge=LEFT, buff=0.15)
        right = VGroup(T("a failure: retried tonight, never stored", 22, C_BAD),
                       M("runner-error · install-failed · disk-full", 19),
                       M("container timeout · the job crashed", 19)).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        VGroup(left, right).arrange(RIGHT, buff=1.2, aligned_edge=UP).move_to(DOWN * 1.65)
        self.play(FadeIn(left))
        self.say("Two outcomes record a result. A flaky-found result names the tests that disagreed.", 2.4)
        self.play(FadeIn(right))
        self.say("Everything else may be the machine's fault, so it is retried and never stored.", 2.2)
        self.play(FadeOut(VGroup(job, fl, bs, arrs, left, right)))

        classes = [("FAST", 5), ("NORMAL", 15), ("SLOW", 45)]
        blocks = VGroup()
        for i, (n, mins) in enumerate(classes):
            bar = Rectangle(width=mins * 0.12, height=0.45, color=C_RUN, fill_color=C_RUN, fill_opacity=0.4,
                            stroke_width=2)
            lab = M(f"{n}", 20).next_to(bar, LEFT, buff=0.25)
            val = T(f"{mins} min", 20).next_to(bar, RIGHT, buff=0.2)
            blocks.add(VGroup(lab, bar, val))
        for i, b in enumerate(blocks):
            b[1].move_to([-1.0 + b[1].width / 2 - 3.4, 1.6 - 0.65 * i, 0])
            b[0].next_to(b[1], LEFT, buff=0.25)
            b[2].next_to(b[1], RIGHT, buff=0.2)
        th = T("deadline classes (ci/deadlines.py)", 22, C_DIM).move_to([-1.0, 2.5, 0])
        slow = T("coverage and stability", 20, C_WARN).next_to(blocks[2], RIGHT, buff=0.4)
        self.play(FadeIn(th), LaggedStart(*[FadeIn(b) for b in blocks], lag_ratio=0.2))
        self.play(FadeIn(slow))
        self.say("Every CI job has one of three deadline classes. Both new runs are SLOW: 45 minutes.", 2.4)
        notes = lines([
            "the deadline is in no key: changing it re-measures nothing",
            "no default anywhere: a job with no deadline class fails to start",
            "a workflow's timeout = 10 min + Σ (each job's deadline + 5 min setup)",
        ], 21, GREY_A, buff=0.22).move_to(DOWN * 1.2)
        self.play(LaggedStart(*[FadeIn(x) for x in notes], lag_ratio=0.3))
        self.say("Workflow timeouts are computed from the same table, so the figures cannot drift apart.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
class S09Sets(Captioned):
    def construct(self):
        self.add(badge(9, "results are sets (decision record 0009)"))

        def store(name, obs, y):
            items = VGroup(*[chip(o, C_MEAS, 20) for o in obs]).arrange(RIGHT, buff=0.15)
            r = SurroundingRectangle(items, buff=0.25, corner_radius=0.12, color=GREY_B, stroke_width=2)
            lab = T(name, 20, C_DIM).next_to(r, LEFT, buff=0.2)
            return VGroup(lab, r, items).move_to([-3.6, y, 0])

        a = store("nightly store", ["r1", "r2"], 1.6)
        b = store("re-run store", ["r2", "r3"], 0.2)
        self.play(FadeIn(a), FadeIn(b))
        self.say("Every coverage and stability result is stored under the digest of its own content.", 2.4)
        u1 = VGroup(T("A then B", 18, C_DIM), chip("{ r1, r2, r3 }", C_OK, 20)).arrange(RIGHT, buff=0.25)
        u2 = VGroup(T("B then A", 18, C_DIM), chip("{ r1, r2, r3 }", C_OK, 20)).arrange(RIGHT, buff=0.25)
        VGroup(u1, u2).arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([3.4, 0.9, 0])
        m1 = arrow(a.get_right(), u1.get_left())
        m2 = arrow(b.get_right(), u2.get_left())
        self.play(GrowArrow(m1), GrowArrow(m2), FadeIn(u1), FadeIn(u2))
        self.say("A manual re-run writes its own store. They merge by union: either order, no conflict.", 2.4)
        contrast = T("a single value, by contrast: passed = true here and false there is a conflict",
                     20, GREY_A).move_to(DOWN * 1.0)
        self.play(FadeIn(fit(contrast, 12.5)))
        self.say("One stored value would have to pick a winner. A set keeps both, and the reader decides.", 2.4)
        self.play(FadeOut(VGroup(a, b, u1, u2, m1, m2, contrast)))

        hd = VGroup(M("outcomes per test, over every stability result", 21, C_MEAS),
                    T("on the reference runner", 17, C_DIM)).arrange(RIGHT, buff=0.4).move_to(UP * 2.4)
        rows = [
            ("test_login", "{ pass }", "", C_OK),
            ("test_upload", "{ fail }", "broken on main: left out", GREY_A),
            ("test_retry", "{ pass, fail }", "flaky: named in the report", C_BAD),
            ("test_export", "{ pass }", "passed in 2 results: one outcome", C_OK),
        ]
        tbl = VGroup()
        for i, (k, v, note, col) in enumerate(rows):
            y = 1.5 - 0.7 * i
            kk = M(k, 20).move_to([0, y, 0]).align_to([-6.0, 0, 0], LEFT)
            vv = M(v, 20, col).move_to([0, y, 0]).align_to([-2.8, 0, 0], LEFT)
            nn = T(note, 19, col).move_to([0, y, 0]).align_to([0.8, 0, 0], LEFT) if note else VGroup()
            tbl.add(VGroup(kk, vv, nn))
        self.play(FadeIn(hd), LaggedStart(*[FadeIn(r[0]) for r in tbl], lag_ratio=0.1))
        self.play(LaggedStart(*[FadeIn(r[1]) for r in tbl], lag_ratio=0.2), FadeIn(tbl[1][2]))
        self.say("The publisher reduces every stability result to the outcomes each test showed.", 2.2)
        self.play(FadeIn(tbl[2][2]), Indicate(tbl[2][1], color=C_BAD))
        self.say("A pass beside a fail makes a test flaky, and no merge order can hide it.", 2.4)
        self.play(FadeIn(tbl[3][2]))
        self.say("A test that passed in two results has one outcome, not two.", 2.0)
        rules = lines(["a run that times out or hits a runner error is retried, never stored",
                       "results never expire: a new run adds to the set, it overwrites nothing"], 21,
                      GREY_A).move_to(DOWN * 1.9)
        self.play(FadeIn(rules))
        self.say("Results are only ever added, so an old smoke.json can always be explained.", 2.4)
        self.clear_all()


# ----------------------------------------------------------------------------
class S10Publish(Captioned):
    def construct(self):
        self.add(badge(10, "publishing under a snapshot"))
        snap = box("publisher, reading snapshot S", C_GEN, w=5.0, h=0.6, size=22).move_to(UP * 2.4)
        self.play(FadeIn(snap))
        self.say("The publisher reads a frozen snapshot S of the store, and judges each suite in it.", 2.0)
        outs = [
            ("coverage-broken, or more than 10% of the tests flaky", "Refused + reasons", C_BAD),
            ("no stability result over S's test list yet", "NotReady", C_WARN),
            ("otherwise", "choose a result", C_OK),
        ]
        rows = VGroup()
        for i, (c, r, col) in enumerate(outs):
            y = 1.35 - 0.75 * i
            cc = fit(T(c, 20), 7.2).move_to([0, y, 0]).align_to([-6.3, 0, 0], LEFT)
            aa = arrow([1.2, y, 0], [1.9, y, 0], color=col)
            rr = T(r, 20, col).move_to([0, y, 0]).align_to([2.1, 0, 0], LEFT)
            rows.add(VGroup(cc, aa, rr))
        caps = [
            "Broken coverage, or over 10% flaky tests, refuses the suite. Its PR jobs run everything.",
            "A suite with no stability result yet is NotReady, and keeps yesterday's file.",
            "Otherwise it judges the results over exactly the tests S lists, on the reference runner.",
        ]
        for r, cap in zip(rows, caps):
            self.play(FadeIn(r, shift=0.1 * RIGHT), run_time=0.7)
            self.say(cap, 2.2)
        rule = T("a test ships only if every such result passed it within budget", 21, C_OK).move_to(DOWN * 0.95)
        self.play(FadeIn(rule))
        self.say("A test ships only if every one of those results passed it.", 2.0)
        pref = VGroup(T("then one result supplies the list, preferring one that", 20, C_DIM),
                      T("1 ships the most stable tests · 2 reaches the most branches · 3 is the newest · "
                        "4 has the smaller id", 19)).arrange(DOWN, buff=0.15).move_to(DOWN * 1.95)
        fit(pref, 13)
        self.play(FadeIn(pref))
        self.say("One result is chosen, by a fixed preference, and its shipped list is written out.", 2.4)
        self.play(FadeOut(VGroup(snap, rows, rule, pref)))

        fields = [
            ("schema_version, commit", "the main commit the list was measured on"),
            ("runner", "{cpus, memory_bytes}, the reference runner's size"),
            ("suite", "the package and its TEST_LIST digest"),
            ("tests", "[{id, file, sha, median_ms}]: the shipped tests, in order"),
            ("coverage", "{branches_total, branches_pre}"),
            ("flaky", "the test ids left out as flaky"),
            ("counts", "candidates, first_cover, run, left_out, too_slow, shipped"),
        ]
        hd = VGroup(M("smoke.json", 24, C_OUT), T("read-only artifact · smoke.schema.json beside it", 18,
                                                  C_DIM)).arrange(RIGHT, buff=0.4).move_to(UP * 2.5)
        tbl = VGroup()
        for i, (k, v) in enumerate(fields):
            y = 1.8 - 0.55 * i
            kk = M(k, 18, C_OUT).move_to([0, y, 0]).align_to([-6.0, 0, 0], LEFT)
            vv = T(v, 18, GREY_A).move_to([0, y, 0]).align_to([-1.2, 0, 0], LEFT)
            tbl.add(VGroup(kk, vv))
        self.play(FadeIn(hd), LaggedStart(*[FadeIn(r, shift=0.1 * RIGHT) for r in tbl], lag_ratio=0.1), run_time=2)
        self.say("The file carries the chosen result, frozen, with everything a reader needs to check it.", 2.4)
        self.say("The publisher refuses a test that no longer exists on main, or a list over its budget.", 2.6)
        self.clear_all()


# ----------------------------------------------------------------------------
class S11Use(Captioned):
    def construct(self):
        self.add(badge(11, "using the smoke suite"))
        art = chip("smoke.json", C_OUT, 20).move_to([-5.4, 1.9, 0])
        checks = [
            "checked against its schema",
            "commit is an ancestor of the pull request's base",
            "the runner is at least the reference runner's size",
        ]
        cs = VGroup(*[T(f"{i + 1}  {c}", 20) for i, c in enumerate(checks)]).arrange(DOWN, aligned_edge=LEFT,
                                                                                       buff=0.2)
        sbox = SurroundingRectangle(cs, buff=0.25, corner_radius=0.12, color=C_RUN, stroke_width=2)
        sl = M("PR job: ci/select.py", 19, C_RUN).next_to(sbox, UP, buff=0.12).align_to(sbox, LEFT)
        grp = VGroup(sl, sbox, cs).move_to([1.0, 1.65, 0])
        a = arrow(art.get_right(), sbox.get_left())
        self.play(FadeIn(art), GrowArrow(a), FadeIn(sbox), FadeIn(sl))
        self.play(LaggedStart(*[FadeIn(c, shift=0.1 * RIGHT) for c in cs], lag_ratio=0.3))
        self.say("The PR job reads the file and fails safe: missing, invalid or stale, it runs the full suite.", 2.4)
        self.say("On a smaller runner it still runs the list, and warns that the budget may not hold.", 2.6)
        self.say("A failing smoke test links to its source file, from tests[].file.", 2.0)

        fn = M("select.tests_for(event)", 22, C_WARN).move_to(DOWN * 0.15)
        u = box2("pull request", "SmokeSuite: the shipped list, in order", C_OK, w=5.4, h=0.85, size=20,
                 sub=17).move_to([-3.2, -1.35, 0])
        lg = box2("merge queue", "FullSuite: every test, in 8 shards", GREY_B, w=5.4, h=0.85,
                  size=20, sub=17).move_to([3.2, -1.35, 0])
        a1 = arrow(fn.get_bottom(), u.get_top())
        a2 = arrow(fn.get_bottom(), lg.get_top())
        self.play(FadeIn(fn))
        self.say("PR jobs and the merge queue draw their tests from one function, the only branch on the event.",
                 2.4)
        self.play(GrowArrow(a1), GrowArrow(a2), FadeIn(u), FadeIn(lg))
        self.say("Re-runs and the flaky-test report read the same list.", 2.0)
        self.say("The PR job's coverage pass covers the same list.", 1.6)
        self.say("So branches_pre and branches_post compare like for like: a PR that loses branches is flagged.", 2.4)
        self.say("The merge queue's full run stays the gate: the smoke suite only gives a fast first answer.", 2.0)
        self.clear_all()


# ----------------------------------------------------------------------------
class S12Review(Captioned):
    def construct(self):
        self.add(badge(12, "how to review it"))
        read = VGroup(T("read first, about 10 minutes", 22, C_OUT),
                      M("docs/design/smoke-suite.md", 19),
                      T("then decision records 0007, 0008, 0009", 19, GREY_A)).arrange(DOWN, aligned_edge=LEFT,
                                                                                  buff=0.15)
        groups = [
            ("1–3", "groundwork: runner sizes, deadline classes"),
            ("4–5", "coverage: per-test contexts and COVERAGE"),
            ("6–8", "stability: the rule, the run and STABILITY"),
            ("9–11", "publishing and use: publisher, smoke.json, PR jobs"),
            ("12", "docs and decision records"),
        ]
        commits = VGroup(T("then the 12 commits, in order", 22, C_OUT), *[
            VGroup(M(n, 18, C_WARN), T(d, 18)).arrange(RIGHT, buff=0.25) for n, d in groups
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        for row in commits[1:]:
            row[1].align_to(commits[1][1], LEFT)
            row[1].shift(RIGHT * (0.95 - (row[1].get_left()[0] - row[0].get_left()[0])))
        left = VGroup(read, commits).arrange(DOWN, aligned_edge=LEFT, buff=0.45).move_to([-2.3, 0.45, 0])
        self.play(FadeIn(read))
        self.say("Start with the design note: about 200 lines, and it describes only what is built.", 2.2)
        self.play(LaggedStart(*[FadeIn(r) for r in commits], lag_ratio=0.12))
        self.say("Then the commits in order. Each builds on its own.", 1.8)

        def section(title, color, items, mono=True, size=17):
            h = T(title, 22, color)
            body = VGroup(*[(M if mono else T)(x, size, WHITE if mono else C_DIM) for x in items])
            fit(body.arrange(DOWN, aligned_edge=LEFT, buff=0.1), 4.2)
            return VGroup(h, body).arrange(DOWN, aligned_edge=LEFT, buff=0.15)

        care = VGroup(section("read carefully", C_BAD, ["ci/greedy.py", "ci/stability.py"]),
                      section("where the reasoning is tested", C_OK, ["test_merge_order.py",
                                                                      "test_stability.py",
                                                                      "test_greedy.py, against brute force"]),
                      section("skip", C_DIM, ["golden files under fixtures/"], mono=False, size=18)
                      ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([4.65, 0.45, 0])
        self.play(FadeIn(care[0]))
        self.say("The lazy greedy and the stability rule are where to slow down. The rule is the core.", 2.4)
        self.play(FadeIn(care[1]))
        self.say("Two-store merges in both orders, the stability rule, and the greedy against brute force.", 2.4)
        self.play(FadeIn(care[2]))
        self.say("The golden files can be skipped.", 1.6)
        size = T("+4,210 lines: 1,640 code · 1,890 tests · 680 docs and decision records",
                 19, GREY_A).move_to(DOWN * 2.75)
        self.play(FadeIn(fit(size, 13)))
        self.say("More than half of the added lines are tests and docs.", 2.0)
        self.clear_all()

        end = VGroup(T("measured once a night, on main", 36),
                     T("keyed only on what it measures", 36),
                     T("published as one file every job reads", 36, C_OUT)).arrange(DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(e, shift=0.1 * UP) for e in end], lag_ratio=0.4), run_time=2)
        self.wait(3)
        self.play(FadeOut(end))
