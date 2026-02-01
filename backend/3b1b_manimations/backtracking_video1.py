import wave
import contextlib
from pathlib import Path

from manimlib import (
    Scene, VGroup, Text, Dot, Line, Rectangle, Circle,
    FadeIn, FadeOut, Write, ShowCreation, GrowFromCenter,
    Transform, Indicate, SurroundingRectangle,
    YELLOW, GREEN, RED, GREY_B, WHITE, ORIGIN, UP, DOWN, LEFT, RIGHT
)

def wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        return wf.getnframes() / float(wf.getframerate())

def safe_wait(scene: Scene, seconds: float, cap: float = 60.0):
    scene.wait(max(0.0, min(seconds, cap)))

def make_node(label: str, color=WHITE):
    dot = Dot(radius=0.06, color=color)
    txt = Text(label, font_size=22, color=color).next_to(dot, RIGHT, buff=0.12)
    return VGroup(dot, txt)

def connect_nodes(a: VGroup, b: VGroup, color=GREY_B):
    return Line(a[0].get_center(), b[0].get_center(), color=color, stroke_width=3)

class BacktrackingCorePattern(Scene):
    def construct(self):
        sounds_dir = Path("assets/sounds")
        narration = sounds_dir / "narration.wav"
        if not narration.exists():
            raise RuntimeError("Missing assets/sounds/narration.wav. Run `python gen_audio.py` first.")
        narration_dur = wav_duration_seconds(narration)

        # --- Visuals ---
        title = Text("Backtracking — the core pattern", font_size=44)
        subtitle = Text("intuition before code", font_size=28, color=GREY_B).next_to(title, DOWN, buff=0.25)
        header = VGroup(title, subtitle).to_edge(UP, buff=0.6)

        maze_box = Rectangle(width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B)
        maze_box.to_edge(LEFT, buff=0.7).shift(DOWN * 0.6)
        maze_label = Text("Maze mental model", font_size=26, color=GREY_B).next_to(maze_box, UP, buff=0.2)

        c = maze_box.get_center()
        j0 = Dot(c + LEFT*1.9 + UP*0.9, color=WHITE)
        j1 = Dot(c + LEFT*0.6 + UP*0.2, color=WHITE)
        j2 = Dot(c + RIGHT*0.9 + UP*0.9, color=WHITE)
        dead = Dot(c + RIGHT*1.7 + UP*0.2, color=RED)
        goal = Dot(c + RIGHT*1.7 + DOWN*0.9, color=GREEN)

        e01 = Line(j0.get_center(), j1.get_center(), color=GREY_B, stroke_width=4)
        e12 = Line(j1.get_center(), j2.get_center(), color=GREY_B, stroke_width=4)
        e2d = Line(j2.get_center(), dead.get_center(), color=GREY_B, stroke_width=4)
        e2g = Line(j2.get_center(), goal.get_center(), color=GREY_B, stroke_width=4)

        start_txt = Text("start", font_size=20, color=GREY_B).next_to(j0, UP, buff=0.15)
        dead_txt = Text("dead end", font_size=20, color=RED).next_to(dead, RIGHT, buff=0.15)
        goal_txt = Text("solution", font_size=20, color=GREEN).next_to(goal, RIGHT, buff=0.15)

        walker = Circle(radius=0.12, color=YELLOW).move_to(j0.get_center())

        maze_group = VGroup(
            maze_box, maze_label,
            e01, e12, e2d, e2g,
            j0, j1, j2, dead, goal,
            start_txt, dead_txt, goal_txt,
            walker
        )

        tree_box = Rectangle(width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B)
        tree_box.to_edge(RIGHT, buff=0.7).shift(DOWN * 0.6)
        tree_label = Text("Recursion tree", font_size=26, color=GREY_B).next_to(tree_box, UP, buff=0.2)

        t_center = tree_box.get_center()
        root = make_node("∅").move_to(t_center + UP*1.2)
        a = make_node("A").move_to(t_center + LEFT*1.4 + UP*0.3)
        b = make_node("B").move_to(t_center + RIGHT*1.4 + UP*0.3)
        a1 = make_node("A→1").move_to(t_center + LEFT*2.0 + DOWN*0.8)
        a2 = make_node("A→2").move_to(t_center + LEFT*0.8 + DOWN*0.8)
        b1 = make_node("B→1").move_to(t_center + RIGHT*0.8 + DOWN*0.8)
        b2 = make_node("B→2").move_to(t_center + RIGHT*2.0 + DOWN*0.8)

        edges = VGroup(
            connect_nodes(root, a),
            connect_nodes(root, b),
            connect_nodes(a, a1),
            connect_nodes(a, a2),
            connect_nodes(b, b1),
            connect_nodes(b, b2),
        )

        tree_group = VGroup(tree_box, tree_label, edges, root, a, b, a1, a2, b1, b2)
        mantra = Text("Try → Recurse → Undo", font_size=34, color=YELLOW).to_edge(DOWN, buff=0.55)

        # --- Audio (single track) ---
        self.add_sound(str(narration), time_offset=0)

        # --- Animations (timed roughly to narration) ---
        self.play(Write(header), run_time=0.9)
        self.play(FadeIn(maze_box), FadeIn(tree_box), FadeIn(maze_label), FadeIn(tree_label), run_time=0.6)

        self.play(FadeIn(VGroup(e01, j0, j1, start_txt, walker)), run_time=1.1)
        self.play(ShowCreation(edges[0]), GrowFromCenter(root), run_time=1.2)

        self.play(FadeIn(VGroup(e12, j2)), run_time=0.5)
        self.play(walker.animate.move_to(j1.get_center()), run_time=0.4)
        self.play(walker.animate.move_to(j2.get_center()), run_time=0.5)

        self.play(ShowCreation(edges[1]), FadeIn(VGroup(a, b)), run_time=0.8)
        self.play(Write(mantra), run_time=0.5)

        self.play(ShowCreation(e2d), FadeIn(dead), FadeIn(dead_txt), run_time=0.5)
        self.play(walker.animate.move_to(dead.get_center()), run_time=0.45)
        self.play(Indicate(dead, color=RED, scale_factor=1.1), run_time=0.35)

        self.play(walker.animate.move_to(j2.get_center()), run_time=0.45)
        self.play(walker.animate.move_to(j1.get_center()), run_time=0.45)

        self.play(ShowCreation(e2g), FadeIn(goal), FadeIn(goal_txt), run_time=0.6)
        self.play(walker.animate.move_to(j2.get_center()), run_time=0.55)
        self.play(walker.animate.move_to(goal.get_center()), run_time=0.8)
        self.play(Indicate(goal, color=GREEN, scale_factor=1.15), run_time=0.5)

        self.play(ShowCreation(VGroup(edges[2], edges[3])), FadeIn(VGroup(a1, a2)), run_time=1.2)
        self.play(ShowCreation(VGroup(edges[4], edges[5])), FadeIn(VGroup(b1, b2)), run_time=1.2)

        path_rect = SurroundingRectangle(VGroup(root, a, a1), color=YELLOW, buff=0.15)
        self.play(ShowCreation(path_rect), run_time=0.5)
        self.play(Transform(path_rect, SurroundingRectangle(VGroup(root, b, b2), color=YELLOW, buff=0.15)), run_time=0.7)
        self.play(FadeOut(path_rect), run_time=0.3)

        complexity = Text("Worst case ≈ b^d", font_size=36, color=WHITE)
        complexity.next_to(tree_box, DOWN, buff=0.25)
        expl = Text("branching factor × depth", font_size=24, color=GREY_B).next_to(complexity, DOWN, buff=0.15)

        self.play(FadeIn(complexity), FadeIn(expl), run_time=0.8)
        self.play(Indicate(complexity, color=YELLOW), run_time=0.6)

        goal_card = VGroup(
            Text("Learning goal:", font_size=28, color=GREY_B),
            Text("Think in choices, recurse, and undo.", font_size=34, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ORIGIN).shift(DOWN*0.2)
        card_box = SurroundingRectangle(goal_card, color=GREY_B, buff=0.35)

        self.play(FadeOut(maze_group), FadeOut(tree_group), FadeOut(mantra),
                  FadeOut(complexity), FadeOut(expl), run_time=0.8)
        self.play(FadeIn(card_box), FadeIn(goal_card), run_time=0.9)

        # Ensure the scene lasts at least as long as narration (cap just in case)
        safe_wait(self, narration_dur)
