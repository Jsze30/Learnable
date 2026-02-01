# ai_gen_video.py

import wave
import contextlib
from pathlib import Path
from typing import Callable, List, Tuple

from manimlib import (
    Scene, VGroup, Text, Dot, Line, Rectangle, Circle,
    FadeIn, FadeOut, Write, ShowCreation, GrowFromCenter,
    Transform, ReplacementTransform, Indicate, SurroundingRectangle,
    YELLOW, GREEN, RED, GREY_B, WHITE, ORANGE, BLUE,
    ORIGIN, UP, DOWN, LEFT, RIGHT
)

# ----------------------------
# Audio helpers
# ----------------------------
def wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        return wf.getnframes() / float(wf.getframerate())

def safe_wait(scene: Scene, seconds: float, cap: float = 120.0):
    """Never let bad durations cause a forever‑wait."""
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

def callout_box(mob, *, color=YELLOW, buff=0.25):
    return SurroundingRectangle(mob, color=color, buff=buff)

def make_node(label: str, color=WHITE):
    dot = Dot(radius=0.07, color=color)
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


class NarratedTimelineScene(Scene):
    """
    Base class: attach narration.wav at t=0 and run a timeline of actions.
    """
    NARRATION_PATH = Path("assets/sounds/narration.wav")

    def get_narration_path(self) -> Path:
        return self.NARRATION_PATH

    def build_timeline(self) -> List[Beat]:
        """
        Override in child classes.
        Return a list of (t, action) beats.
        """
        return []

    def construct(self):
        narration = self.get_narration_path()
        if not narration.exists():
            raise RuntimeError(
                f"Missing {narration}. Run ai_gen_audio.py first."
            )

        dur = wav_duration_seconds(narration)
        self.add_sound(str(narration), time_offset=0)

        timeline = sorted(self.build_timeline(), key=lambda x: x[0])

        t_prev = 0.0
        for t, action in timeline:
            safe_wait(self, t - t_prev)
            action()
            t_prev = t

        safe_wait(self, dur - t_prev)


# ----------------------------
# Video 1 – What is Backtracking?
# ----------------------------
class Video1(NarratedTimelineScene):
    """
    Implements the first micro‑lecture: “What is Backtracking? The Explorer’s Mindset”.
    """

    def build_timeline(self) -> List[Beat]:
        # -----------------------
        # Static content
        # -----------------------
        title = title_card(
            "What is Backtracking?",
            "The Explorer’s Mindset"
        ).to_edge(UP, buff=0.6)

        # Decision‑tree area (center)
        tree_center = ORIGIN + UP * 0.3
        root = make_node("root").move_to(tree_center + UP * 1.2)

        # Pre‑create a small binary tree (depth 3) – we will reveal it gradually
        lvl1_left = make_node("L").move_to(tree_center + LEFT * 2 + UP * 0.3)
        lvl1_right = make_node("R").move_to(tree_center + RIGHT * 2 + UP * 0.3)

        lvl2_ll = make_node("LL").move_to(tree_center + LEFT * 3 + DOWN * 0.8)
        lvl2_lr = make_node("LR").move_to(tree_center + LEFT * 1 + DOWN * 0.8)
        lvl2_rl = make_node("RL").move_to(tree_center + RIGHT * 1 + DOWN * 0.8)
        lvl2_rr = make_node("RR").move_to(tree_center + RIGHT * 3 + DOWN * 0.8)

        # Edges (invisible at first)
        edges = [
            connect_nodes(root, lvl1_left),
            connect_nodes(root, lvl1_right),
            connect_nodes(lvl1_left, lvl2_ll),
            connect_nodes(lvl1_left, lvl2_lr),
            connect_nodes(lvl1_right, lvl2_rl),
            connect_nodes(lvl1_right, lvl2_rr),
        ]

        # Rope‑metaphor illustration (bottom)
        rope_box = Rectangle(width=6, height=2.5, stroke_width=2, stroke_color=GREY_B)
        rope_box.to_edge(DOWN, buff=0.8)
        rope_label = simple_box_label(rope_box, "Maze Explorer with Rope")

        explorer = Circle(radius=0.25, color=ORANGE).move_to(rope_box.get_left() + RIGHT * 0.5 + DOWN * 0.3)
        rope = Line(explorer.get_center(), rope_box.get_left() + RIGHT * 0.2, color=YELLOW, stroke_width=4)

        # Outro card
        outro = VGroup(
            Text("Key Takeaway:", font_size=30, color=GREY_B),
            Text(
                "Backtracking = depth‑first search + retreat on dead‑ends",
                font_size=34,
                color=WHITE,
            ),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ORIGIN)

        # -----------------------
        # Helper actions
        # -----------------------
        def show_title():
            self.play(Write(title), run_time=1.0)

        def grow_tree():
            # reveal root and first level
            self.play(GrowFromCenter(root), run_time=0.6)
            self.play(ShowCreation(edges[0]), ShowCreation(edges[1]), run_time=0.8)
            self.play(GrowFromCenter(lvl1_left), GrowFromCenter(lvl1_right), run_time=0.8)

        def expand_tree():
            # reveal second level
            self.play(
                ShowCreation(edges[2]), ShowCreation(edges[3]),
                ShowCreation(edges[4]), ShowCreation(edges[5]),
                run_time=1.0,
            )
            self.play(
                GrowFromCenter(lvl2_ll), GrowFromCenter(lvl2_lr),
                GrowFromCenter(lvl2_rl), GrowFromCenter(lvl2_rr),
                run_time=1.0,
            )

        def traverse_highlight():
            # depth‑first visit order: root → L → LL → backtrack → LR → backtrack → backtrack → R → RL → backtrack → RR
            order = [root, lvl1_left, lvl2_ll, lvl2_lr, lvl1_right, lvl2_rl, lvl2_rr]
            for node in order:
                self.play(Indicate(node, color=GREEN, scale_factor=1.2), run_time=0.6)

        def backtrack_demo():
            # show a backtrack from a dead leaf (LL) back to its parent (L)
            highlight = callout_box(lvl2_ll, color=RED)
            self.play(ShowCreation(highlight), run_time=0.4)
            self.play(FadeOut(highlight), run_time=0.3)

        def show_rope_metaphor():
            self.play(FadeIn(rope_box), FadeIn(rope_label), FadeIn(explorer), FadeIn(rope), run_time=0.9)
            # simulate moving forward
            path = [
                explorer.get_center() + RIGHT * 1.5,
                explorer.get_center() + RIGHT * 3.0,
                explorer.get_center() + RIGHT * 4.5,
            ]
            for pt in path:
                self.play(
                    explorer.animate.move_to(pt),
                    rope.animate.put_start_and_end_on(
                        explorer.get_center(),
                        rope_box.get_left() + RIGHT * 0.2
                    ),
                    run_time=0.7,
                )
            # simulate hitting wall and pulling back
            self.play(
                explorer.animate.move_to(rope_box.get_left() + RIGHT * 0.5),
                rope.animate.put_start_and_end_on(
                    explorer.get_center(),
                    rope_box.get_left() + RIGHT * 0.2
                ),
                run_time=0.9,
            )
            self.play(FadeOut(VGroup(rope_box, rope_label, explorer, rope)), run_time=0.6)

        def show_outro():
            box = callout_box(outro, color=YELLOW)
            self.play(FadeIn(outro), run_time=0.8)
            self.play(ShowCreation(box), run_time=0.4)
            self.play(FadeOut(box), run_time=0.3)

        # -----------------------
        # Beats – timestamps (seconds from start of narration)
        # Adjust these numbers after listening to the generated narration.wav
        # -----------------------
        return [
            (0.0, show_title),                 # intro title
            (2.0, grow_tree),                  # "decision tree" intro
            (6.0, expand_tree),                # continue tree growth
            (10.0, traverse_highlight),        # depth‑first traversal
            (15.0, backtrack_demo),            # dead‑end backtrack
            (18.0, show_rope_metaphor),        # rope metaphor
            (24.0, show_outro),                # outro / key pattern
        ]