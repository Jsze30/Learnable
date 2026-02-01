"""
video_template.py

Reusable ManimGL template for narrated micro-lectures.

Assumes you already generated:
  assets/sounds/narration.wav

Recommended workflow:
1) Write narration segments -> gen_audio.py -> narration.wav
2) Define beat timestamps (roughly) below
3) Build visuals with helper functions
4) Render with manimgl
5) Mux audio with ffmpeg (recommended)

Run:
  manimgl video_template.py TemplateVideo -w
"""

import wave
import contextlib
from pathlib import Path
from typing import Callable, List, Tuple

from manimlib import (
    Scene, VGroup, Text, Dot, Line, Rectangle, Circle,
    FadeIn, FadeOut, Write, ShowCreation, GrowFromCenter,
    Transform, ReplacementTransform, Indicate, SurroundingRectangle,
    YELLOW, GREEN, RED, GREY_B, WHITE, ORIGIN, UP, DOWN, LEFT, RIGHT
)

# ----------------------------
# Audio helpers
# ----------------------------
def wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        return wf.getnframes() / float(wf.getframerate())

def safe_wait(scene: Scene, seconds: float, cap: float = 120.0):
    """Never let bad durations cause a forever-wait."""
    scene.wait(max(0.0, min(seconds, cap)))


# ----------------------------
# Reusable visual helpers
# ----------------------------
def title_card(title: str, subtitle: str = "", *, title_size=48, subtitle_size=28):
    t = Text(title, font_size=title_size, color=WHITE)
    if subtitle.strip():
        s = Text(subtitle, font_size=subtitle_size, color=GREY_B).next_to(t, DOWN, buff=0.25)
        return VGroup(t, s)
    return VGroup(t)

def section_header(text: str):
    return Text(text, font_size=34, color=WHITE).to_edge(UP, buff=0.65)

def callout_box(mob, *, color=YELLOW, buff=0.25):
    return SurroundingRectangle(mob, color=color, buff=buff)

def make_node(label: str, color=WHITE):
    dot = Dot(radius=0.06, color=color)
    txt = Text(label, font_size=22, color=color).next_to(dot, RIGHT, buff=0.12)
    return VGroup(dot, txt)

def connect_nodes(a: VGroup, b: VGroup, color=GREY_B, stroke_width=3):
    return Line(a[0].get_center(), b[0].get_center(), color=color, stroke_width=stroke_width)

def simple_box_label(box: Rectangle, label: str):
    return Text(label, font_size=26, color=GREY_B).next_to(box, UP, buff=0.2)


# ----------------------------
# Timeline / Beat system
# ----------------------------
Beat = Tuple[float, Callable[[], None]]
"""
Each beat is (time_in_seconds_from_start, function_to_run).

You define beats in build_timeline().
The engine plays them in order, waiting between timestamps.
"""

# Note: don't change this class name!!
class NarratedTimelineScene(Scene):
    """
    Base class: attach narration.wav at t=0 and run a timeline of actions.
    """
    NARRATION_PATH = Path("assets/sounds/narration.wav")

    def get_narration_path(self) -> Path:
        return self.NARRATION_PATH

    def build_timeline(self) -> List[Beat]:
        """
        Override this in child classes.
        Return a list of (t, action) beats.
        """
        return []

    def construct(self):
        narration = self.get_narration_path()
        if not narration.exists():
            raise RuntimeError(
                f"Missing {narration}. Run your gen_audio.py first."
            )

        dur = wav_duration_seconds(narration)
        self.add_sound(str(narration), time_offset=0)

        timeline = sorted(self.build_timeline(), key=lambda x: x[0])

        # Run beats in order
        t_prev = 0.0
        for t, action in timeline:
            safe_wait(self, t - t_prev)
            action()
            t_prev = t

        # Ensure scene lasts through narration
        safe_wait(self, dur - t_prev)


# ----------------------------
# Example: plug in ANY topic here
# ----------------------------
class TemplateVideo(NarratedTimelineScene):
    """
    Reusable template scene.
    Replace the placeholder visuals + beats with your own.
    """

    def build_timeline(self) -> List[Beat]:
        # ---------- Customize these ----------
        VIDEO_TITLE = "YOUR VIDEO TITLE"
        VIDEO_SUBTITLE = "short tagline or learning goal"
        # -------------------------------------

        # Pre-build reusable objects (so actions can reference them)
        header = title_card(VIDEO_TITLE, VIDEO_SUBTITLE).to_edge(UP, buff=0.6)

        left_box = Rectangle(width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B)
        left_box.to_edge(LEFT, buff=0.7).shift(DOWN * 0.6)
        left_label = simple_box_label(left_box, "Left visual (example)")

        right_box = Rectangle(width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B)
        right_box.to_edge(RIGHT, buff=0.7).shift(DOWN * 0.6)
        right_label = simple_box_label(right_box, "Right visual (example)")

        # Example mini-diagram in left box (replace with your own)
        c = left_box.get_center()
        a = Dot(c + LEFT*1.4 + UP*0.8, color=WHITE)
        b = Dot(c + RIGHT*1.4 + DOWN*0.4, color=WHITE)
        arrow = Line(a.get_center(), b.get_center(), color=GREY_B, stroke_width=4)

        # Example mini-tree in right box
        tc = right_box.get_center()
        root = make_node("root").move_to(tc + UP*1.0)
        n1 = make_node("choice 1").move_to(tc + LEFT*1.3 + DOWN*0.1)
        n2 = make_node("choice 2").move_to(tc + RIGHT*1.3 + DOWN*0.1)
        e1 = connect_nodes(root, n1)
        e2 = connect_nodes(root, n2)

        mantra = Text("Key pattern / mantra", font_size=34, color=YELLOW).to_edge(DOWN, buff=0.55)

        # Helper actions (so beats stay clean)
        def show_title():
            self.play(Write(header), run_time=0.9)

        def show_layout():
            self.play(
                FadeIn(left_box), FadeIn(right_box),
                FadeIn(left_label), FadeIn(right_label),
                run_time=0.6
            )

        def show_left_diagram():
            self.play(FadeIn(a), FadeIn(b), ShowCreation(arrow), run_time=0.9)
            self.play(Indicate(arrow, color=YELLOW), run_time=0.5)

        def show_right_diagram():
            self.play(GrowFromCenter(root), run_time=0.5)
            self.play(ShowCreation(e1), FadeIn(n1), run_time=0.6)
            self.play(ShowCreation(e2), FadeIn(n2), run_time=0.6)

        def show_mantra():
            self.play(Write(mantra), run_time=0.6)

        def emphasize_then_wrap():
            box = callout_box(mantra, color=YELLOW)
            self.play(ShowCreation(box), run_time=0.4)
            self.play(FadeOut(box), run_time=0.3)

            end_card = VGroup(
                Text("Wrap-up:", font_size=28, color=GREY_B),
                Text("One sentence takeaway.", font_size=34, color=WHITE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ORIGIN).shift(DOWN*0.2)
            end_box = SurroundingRectangle(end_card, color=GREY_B, buff=0.35)

            self.play(
                FadeOut(VGroup(left_box, right_box, left_label, right_label, a, b, arrow, root, n1, n2, e1, e2)),
                FadeOut(mantra),
                run_time=0.8
            )
            self.play(FadeIn(end_box), FadeIn(end_card), run_time=0.9)

        # ----------------------------
        # Beats (edit these times)
        # ----------------------------
        # These timestamps are from narration start (t=0).
        # You can refine by printing durations from gen_audio.py and adjusting.
        return [
            (0.0, show_title),
            (0.9, show_layout),
            (2.0, show_left_diagram),
            (5.0, show_right_diagram),
            (8.0, show_mantra),
            (12.0, emphasize_then_wrap),
        ]
