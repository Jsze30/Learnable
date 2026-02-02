# ai_gen_video.py
# [ ] Only ManimGL documented/template APIs used
# [ ] Class name is Video2
# [ ] Narration audio loaded from ai_gen_audio.py output (narration.wav)
# [ ] Sync uses explicit beats / waits
# [ ] No overly complex animations
# [ ] On-screen layout safe and readable
# [ ] Produces mp4 via template’s method

import wave
import contextlib
from pathlib import Path
from typing import Callable, List, Tuple, Optional

from manimlib import (
    Scene, VGroup, Text, Dot, Line, Rectangle,
    FadeIn, FadeOut, Write, ShowCreation, GrowFromCenter,
    Indicate, SurroundingRectangle,
    YELLOW, GREY_B, WHITE, ORIGIN, UP, DOWN, LEFT, RIGHT
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
# Clearing helpers (CRITICAL)
# ----------------------------
def clear_group(scene: Scene, group: VGroup, *, run_time: float = 0.6):
    """
    Explicitly clears a visual region.
    ALWAYS call this before drawing new visuals
    in the same screen location.
    """
    if group is None or len(group) == 0:
        return
    scene.play(FadeOut(group), run_time=run_time)
    scene.remove(group)


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
        """Override in child classes."""
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
# Video 2: Backtracking in Action – n‑Queens
# ----------------------------
class Video2(NarratedTimelineScene):
    def build_timeline(self) -> List[Beat]:
        # ----------------------------
        # Static layout objects
        # ----------------------------
        header = title_card(
            "Backtracking in Action: Solving the n‑Queens Puzzle",
            "How a simple recursive search finds all solutions"
        ).to_edge(UP, buff=0.6)

        # Left region – chessboard illustration
        left_box = Rectangle(
            width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B
        ).to_edge(LEFT, buff=0.7).shift(DOWN * 0.6)
        left_label = simple_box_label(left_box, "Board (row‑by‑row)")

        # Right region – decision tree illustration
        right_box = Rectangle(
            width=5.4, height=3.4, stroke_width=3, stroke_color=GREY_B
        ).to_edge(RIGHT, buff=0.7).shift(DOWN * 0.6)
        right_label = simple_box_label(right_box, "Decision Tree")

        # ----------------------------
        # Board states (simple text diagrams)
        # ----------------------------
        def board_text(state: List[Optional[int]]) -> Text:
            """
            state[i] = column index of queen in row i (0‑based) or None.
            """
            rows = []
            n = 4  # 4×4 board – enough to illustrate the idea
            for r in range(n):
                cols = []
                for c in range(n):
                    if state[r] is not None and state[r] == c:
                        cols.append("Q")
                    else:
                        cols.append(".")
                rows.append(" ".join(cols))
            return Text("\n".join(rows), font_size=28, color=WHITE, alignment="LEFT")

        board_empty = board_text([None, None, None, None])
        board_row1 = board_text([1, None, None, None])          # queen at (0,1)
        board_row1_row2 = board_text([1, 3, None, None])       # second queen placed safely
        board_conflict = board_text([1, 2, None, None])        # conflict example (same diagonal)
        board_backtrack = board_text([1, None, None, None])    # after backtrack

        # Group each state for easy clearing
        board_states = {
            "empty": VGroup(board_empty),
            "row1": VGroup(board_row1),
            "row1_row2": VGroup(board_row1_row2),
            "conflict": VGroup(board_conflict),
            "backtrack": VGroup(board_backtrack),
        }

        # Position boards inside left box
        for grp in board_states.values():
            grp.move_to(left_box.get_center())

        # ----------------------------
        # Decision‑tree diagram (very small)
        # ----------------------------
        tc = right_box.get_center()
        root = make_node("row 1").move_to(tc + UP * 1.0)
        c1 = make_node("col 1").move_to(tc + LEFT * 1.3 + DOWN * 0.2)
        c2 = make_node("col 2").move_to(tc + RIGHT * 1.3 + DOWN * 0.2)
        e1 = connect_nodes(root, c1)
        e2 = connect_nodes(root, c2)
        tree_group = VGroup(root, c1, c2, e1, e2)

        # ----------------------------
        # Tracking active groups for clearing
        # ----------------------------
        active_left: Optional[VGroup] = None
        active_right: Optional[VGroup] = None

        # ----------------------------
        # Helper actions (kept short)
        # ----------------------------
        def show_title():
            self.play(Write(header), run_time=0.9)

        def show_layout():
            self.play(
                FadeIn(left_box), FadeIn(right_box),
                FadeIn(left_label), FadeIn(right_label),
                run_time=0.6,
            )

        # ----- LEFT (board) actions -----
        def show_board(state_key: str):
            nonlocal active_left
            if active_left is not None:
                clear_group(self, active_left, run_time=0.5)
            grp = board_states[state_key]
            self.play(FadeIn(grp), run_time=0.8)
            active_left = grp

        def clear_left():
            nonlocal active_left
            if active_left is not None:
                clear_group(self, active_left, run_time=0.5)
                active_left = None

        # ----- RIGHT (tree) actions -----
        def show_tree():
            nonlocal active_right
            if active_right is not None:
                clear_group(self, active_right, run_time=0.5)
            self.play(GrowFromCenter(root), run_time=0.5)
            self.play(ShowCreation(e1), FadeIn(c1), run_time=0.6)
            self.play(ShowCreation(e2), FadeIn(c2), run_time=0.6)
            active_right = tree_group

        def clear_right():
            nonlocal active_right
            if active_right is not None:
                clear_group(self, active_right, run_time=0.5)
                active_right = None

        # ----- Wrap‑up -----
        def emphasize_then_wrap():
            # Callout on the key pattern
            mantra = Text(
                "Backtrack → Try → Reject → Re‑try", font_size=34, color=YELLOW
            ).to_edge(DOWN, buff=0.55)
            box = callout_box(mantra, color=YELLOW)
            self.play(Write(mantra), run_time=0.7)
            self.play(ShowCreation(box), run_time=0.4)
            self.play(FadeOut(box), run_time=0.3)

            # End card
            end_card = VGroup(
                Text("Wrap‑up:", font_size=28, color=GREY_B),
                Text(
                    "Backtracking explores all possibilities depth‑first.",
                    font_size=34,
                    color=WHITE,
                ),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(ORIGIN).shift(DOWN * 0.2)
            end_box = SurroundingRectangle(end_card, color=GREY_B, buff=0.35)

            # Clear everything else
            clear_left()
            clear_right()
            self.play(
                FadeOut(VGroup(left_box, left_label, right_box, right_label)),
                FadeOut(mantra),
                run_time=0.8,
            )
            self.play(FadeIn(end_box), FadeIn(end_card), run_time=0.9)

        # ----------------------------
        # Beats (times are approximate, based on narration)
        # ----------------------------
        return [
            (0.0, show_title),                     # "In this video we’ll see..."
            (1.0, show_layout),                    # "We represent the board..."
            (2.5, lambda: show_board("empty")),   # show empty board
            (4.0, lambda: show_board("row1")),    # place first queen
            (6.0, lambda: show_board("row1_row2")),  # safe second queen
            (8.0, lambda: show_board("conflict")),   # illustrate conflict
            (10.0, lambda: show_board("backtrack")), # backtrack step
            (12.0, show_tree),                     # show decision tree
            (16.0, emphasize_then_wrap),           # final mantra & wrap‑up
        ]