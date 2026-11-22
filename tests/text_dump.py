"""A clean scene for say(anims=...) and the text dump. tests/test_layout.sh expects no warnings and every text listed."""

from pr3b1b import *


class Steps(Captioned):
    def construct(self):
        self.add(badge(1, "captions and steps"))
        a = box("first step", BLUE_C).move_to(LEFT * 3.5)
        b = box("second step", GREEN_C).move_to(RIGHT * 3.5)
        self.say("A step and its caption arrive in one play.", anims=[FadeIn(a)])
        link = arrow(a.get_right(), b.get_left())
        self.say("Then the second step, with its 42 items.", 1.5, anims=[GrowArrow(link), FadeIn(b)])
        self.clear_all()
