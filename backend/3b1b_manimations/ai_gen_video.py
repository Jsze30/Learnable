# ai_gen_video.py

import wave
import contextlib
from pathlib import Path
from typing import Callable, List, Tuple

from manimlib import (
    Scene, VGroup, Text, Dot, Line, Rectangle, Circle,
    FadeIn, FadeOut, Write, ShowCreation, GrowFromCenter,
    Transform, ReplacementTransform, Indicate, SurroundingRectangle,
    ApplyMethod,
    YELLOW, GREEN, RED, GREY_B, WHITE, ORIGIN,
    UP, DOWN, LEFT, RIGHT
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


class NarratedTimelineScene(Scene):
    """
    Base class: attach narration.wav at t=0 and run a timeline of actions.
    """
    NARRATION_PATH = Path("assets/sounds/narration.wav")

    def get_narration_path(self) -> Path:
        return self.NARRATION_PATH

    def build_timeline(self) -> List[Beat]:
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

        t_prev = 0.0
        for t, action in timeline:
            safe_wait(self, t - t_prev)
            action()
            t_prev = t

        safe_wait(self, dur - t_prev)


# ----------------------------
# Video 1 – “What Is Backtracking? The “Try‑Everything” Mindset”
# ----------------------------
class Video1(NarratedTimelineScene):
    def build_timeline(self) -> List[Beat]:
        # -------------------------------------------------
        # Determine timestamps from individual segment files
        # -------------------------------------------------
        seg_files = ["intro.wav", "contrast.wav", "maze.wav", "dfs.wav"]
        seg_paths = [Path("assets/sounds") / f for f in seg_files]
        seg_durs = [wav_duration_seconds(p) for p in seg_paths]

        # cumulative start times
        starts = [0.0]
        for d in seg_durs[:-1]:
            starts.append(starts[-1] + d)

        # -------------------------------------------------
        # Pre‑build visual objects (shared across beats)
        # -------------------------------------------------
        # Title
        header = title_card(
            "What Is Backtracking?",
            "The “Try‑Everything” Mindset"
        ).to_edge(UP, buff=0.6)

        # Definition segment (intro)
        def_text = Text(
            "Backtracking is a systematic brute‑force search.\n"
            "We build a solution piece‑by‑piece, and whenever a partial\n"
            "choice violates a constraint we step back and try a different option.",
            font_size=28,
            color=WHITE,
            line_spacing=0.8
        ).to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)

        # Simple diagram for definition
        d_center = LEFT * 3 + DOWN * 1
        part_a = Dot(d_center + LEFT * 1.5, color=GREEN)
        part_b = Dot(d_center + RIGHT * 1.5, color=GREEN)
        part_arrow = Line(part_a.get_center(), part_b.get_center(), color=GREY_B, stroke_width=3)
        backtrack_arrow = Line(part_b.get_center(), part_a.get_center(), color=RED, stroke_width=3, dash_length=0.1)

        # Contrast segment
        # Greedy path (straight line)
        greedy_line = Line(LEFT * 4 + UP * 1, LEFT * 2 + UP * 1, color=YELLOW, stroke_width=4)
        greedy_label = Text("Greedy / Heuristic", font_size=24, color=YELLOW).next_to(greedy_line, UP)

        # Exhaustive tree (binary tree)
        tree_root = make_node("root").move_to(RIGHT * 2 + UP * 1.5)
        left_child = make_node("L").move_to(RIGHT * 1 + UP * 0.5)
        right_child = make_node("R").move_to(RIGHT * 3 + UP * 0.5)
        edge_l = connect_nodes(tree_root, left_child)
        edge_r = connect_nodes(tree_root, right_child)
        tree_group = VGroup(tree_root, left_child, right_child, edge_l, edge_r)
        tree_label = Text("Exhaustive Search", font_size=24, color=GREY_B).next_to(tree_group, UP)

        # Maze segment
        # Build a tiny 3x3 grid (9 squares)
        squares = VGroup(*[
            Rectangle(width=0.8, height=0.8, stroke_width=2, stroke_color=GREY_B)
            .move_to(LEFT * 2 + DOWN * 2 + 0.9 * (i % 3) * RIGHT + 0.9 * (i // 3) * UP)
            for i in range(9)
        ])
        explorer = Dot(radius=0.12, color=YELLOW).move_to(squares[0].get_center())
        maze_label = Text("Maze Explorer", font_size=24, color=WHITE).to_edge(UP, buff=0.8)

        # DFS recursion tree segment
        # Binary tree depth 3
        nodes = []
        edges = []
        for depth in range(3):
            for i in range(2 ** depth):
                label = f"N{depth}_{i}"
                node = make_node(label).move_to(LEFT * 3 + RIGHT * (i * 1.5) + UP * (2 - depth) * 1.2)
                nodes.append(node)
                if depth > 0:
                    parent_idx = (i // 2) + sum(2 ** d for d in range(depth - 1))
                    edge = connect_nodes(nodes[parent_idx], node)
                    edges.append(edge)
        tree = VGroup(*nodes, *edges)
        dfs_label = Text("Depth‑First Traversal", font_size=24, color=WHITE).to_edge(UP, buff=0.8)

        # End card
        end_card = VGroup(
            Text("Take‑away:", font_size=30, color=GREY_B),
            Text("Backtracking = try everything, prune when impossible.", font_size=34, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ORIGIN)
        end_box = SurroundingRectangle(end_card, color=GREY_B, buff=0.35)

        # -------------------------------------------------
        # Action helpers
        # -------------------------------------------------
        def show_title():
            self.play(Write(header), run_time=1.0)

        def show_definition():
            self.play(FadeIn(def_text), run_time=1.2)
            self.play(FadeIn(part_a), FadeIn(part_b), ShowCreation(part_arrow), run_time=0.8)
            self.play(Indicate(backtrack_arrow, color=RED), run_time=0.6)

        def show_contrast():
            self.play(FadeIn(greedy_line), FadeIn(greedy_label), run_time=0.8)
            self.play(FadeIn(tree_group), FadeIn(tree_label), run_time=0.9)

        def show_maze():
            self.play(FadeIn(squares), FadeIn(maze_label), run_time=0.9)
            self.play(FadeIn(explorer), run_time=0.5)
            # simple path: forward 2 steps, backtrack, forward another
            path = [
                squares[0].get_center(),
                squares[1].get_center(),
                squares[2].get_center(),
                squares[5].get_center(),
                squares[4].get_center(),
                squares[3].get_center(),
                squares[6].get_center(),
            ]
            for pt in path:
                self.play(ApplyMethod(explorer.move_to, pt), run_time=0.4)
            self.play(Indicate(explorer, color=RED), run_time=0.5)

        def show_dfs():
            self.play(FadeIn(tree), FadeIn(dfs_label), run_time=1.0)
            # simulate depth‑first traversal with a highlight dot
            highlight = Dot(radius=0.09, color=YELLOW).move_to(nodes[0][0].get_center())
            self.play(FadeIn(highlight), run_time=0.5)
            order = [0, 1, 3, 4, 2, 5, 6]  # pre‑order indices of nodes list
            for idx in order:
                target = nodes[idx][0].get_center()
                self.play(ApplyMethod(highlight.move_to, target), run_time=0.4)
            self.play(FadeOut(highlight), run_time=0.4)

        def wrap_up():
            self.play(
                FadeOut(VGroup(header, def_text, part_a, part_b, part_arrow, backtrack_arrow,
                               greedy_line, greedy_label, tree_group, tree_label,
                               squares, explorer, maze_label,
                               tree, dfs_label)),
                run_time=0.8
            )
            self.play(FadeIn(end_box), FadeIn(end_card), run_time=1.0)

        # -------------------------------------------------
        # Beats (using computed start times)
        # -------------------------------------------------
        beats: List[Beat] = [
            (starts[0] + 0.0, show_title),
            (starts[0] + 0.5, show_definition),
            (starts[1] + 0.2, show_contrast),
            (starts[2] + 0.2, show_maze),
            (starts[3] + 0.2, show_dfs),
            (starts[3] + seg_durs[3] - 2.0, wrap_up),  # start wrap‑up ~2 s before audio ends
        ]

        return beats