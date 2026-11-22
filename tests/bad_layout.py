"""Scenes with planted layout problems. tests/test_layout.sh expects the check to report each one."""

from pr3b1b import *


class BadFrame(Captioned):
    def construct(self):
        self.add(badge(1, "a bad scene"))
        off = T("this label runs right off the edge of the frame", 30).move_to(RIGHT * 4)
        a = T("overlapping one", 24).move_to(UP * 1)
        b = T("overlapping two", 24).move_to(UP * 1.05 + RIGHT * 0.3)
        tiny = T("tiny", 10).move_to(LEFT * 3)
        low = box("sits in the caption band", BLUE_C).move_to(DOWN * 3.3)
        squeezed = fit(T("a very long label squeezed into a small box until unreadable", 24), 2)
        self.play(FadeIn(off), FadeIn(a), FadeIn(b), FadeIn(tiny), FadeIn(low), FadeIn(squeezed))
        self.say("A caption that is fine.")
        self.say("This caption is much, much too long for one line at the bottom of the screen, "
                 "so it shrinks a lot, and you should split it.")
        self.clear_all()


class BadLines(Captioned):
    def construct(self):
        self.add(badge(2, "more bad layout"))
        src = code(["def f(x):", "    if x:", "", "        return 1", "    return 0"], 20).move_to(LEFT * 4 + UP * 1)
        hl = SurroundingRectangle(src[1], buff=0.12, color=C_WARN)  # taller than the line gap: cuts neighbours
        a = T("a left label", 24).move_to(RIGHT * 2 + UP * 2)
        b = T("a right label", 24).next_to(a, RIGHT, buff=0.0)  # touches a
        lab = T("label under an arrow", 22).move_to(RIGHT * 2 + DOWN * 1)
        ar = arrow(RIGHT * 2 + DOWN * 0.2, RIGHT * 2 + DOWN * 1.8)
        gone = T("removed", 22).move_to(RIGHT * 2 + UP * 0.5)
        st = strike(gone)  # a strike-through is meant to cross its text: no warning
        ok = box("a fine box", BLUE_C).move_to(DOWN * 2.3 + LEFT * 3)
        self.play(FadeIn(src), Create(hl), FadeIn(a), FadeIn(b), FadeIn(lab), GrowArrow(ar), FadeIn(gone),
                  Create(st), FadeIn(ok))
        self.say("One caption.")
        self.clear_all()
