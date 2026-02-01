"""
ai_gen_audio.py

Generate narration audio for Video 1 of the Backtracking Algorithms micro‑series
using Deepgram TTS. Run once before rendering the Manim video.

Requirements:
- export DEEPGRAM_API_KEY="your_key"
- pip install requests
"""

import os
import wave
import contextlib
from pathlib import Path
from typing import List, Tuple

import requests

# ----------------------------
# Configuration
# ----------------------------
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"
DEFAULT_MODEL = "aura-2-thalia-en"

OUTPUT_DIR = Path("assets/sounds")
FINAL_AUDIO_NAME = "narration.wav"


# ----------------------------
# WAV utilities
# ----------------------------
def wav_duration_seconds(path: Path) -> float:
    """Return duration of a WAV file in seconds."""
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        return wf.getnframes() / float(wf.getframerate())


def concat_wavs(wav_paths: List[Path], out_path: Path):
    """
    Concatenate WAV files.
    All WAVs must share sample rate, channels, and sample width.
    """
    if not wav_paths:
        raise ValueError("No WAV files provided for concatenation.")

    with wave.open(str(wav_paths[0]), "rb") as w0:
        base_params = w0.getparams()

    frames = []
    for p in wav_paths:
        with wave.open(str(p), "rb") as w:
            if w.getparams()[:4] != base_params[:4]:
                raise RuntimeError(f"WAV format mismatch: {p.name}")
            frames.append(w.readframes(w.getnframes()))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as out:
        out.setparams(base_params)
        for fr in frames:
            out.writeframes(fr)


# ----------------------------
# Deepgram TTS
# ----------------------------
def tts_to_wav(
    text: str,
    out_path: Path,
    model: str = DEFAULT_MODEL,
) -> float:
    """
    Generate a WAV file from text using Deepgram TTS.
    Returns duration in seconds.
    """
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing DEEPGRAM_API_KEY. "
            "Run: export DEEPGRAM_API_KEY='your_key'"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = {
        "model": model,
        "encoding": "linear16",
        "container": "wav",
    }
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}

    response = requests.post(
        DEEPGRAM_TTS_URL,
        params=params,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    out_path.write_bytes(response.content)
    return wav_duration_seconds(out_path)


# ----------------------------
# User content (EDIT THIS)
# ----------------------------
def narration_segments() -> List[Tuple[str, str]]:
    """
    Return a list of (text, filename) pairs for Video 1.
    Filenames should end with .wav.
    """
    return [
        (
            "Welcome to the first video in our backtracking series. "
            "Today we’ll explore the core idea behind backtracking: "
            "systematically trying every possibility, but stepping back "
            "as soon as we hit a dead end.",
            "intro.wav",
        ),
        (
            "Think of a decision tree. Each node represents a partial solution, "
            "and each branch represents a choice. "
            "Backtracking walks this tree depth‑first, building a solution piece by piece.",
            "tree_intro.wav",
        ),
        (
            "When a choice leads to an invalid state, we backtrack: "
            "return to the previous node and explore the next branch. "
            "This guarantees an exhaustive search of the solution space.",
            "backtrack_explain.wav",
        ),
        (
            "A useful mental model is a maze explorer with a rope. "
            "You walk forward, laying rope behind you. "
            "If you hit a wall, you pull the rope back to the last fork and try a different path.",
            "rope_metaphor.wav",
        ),
        (
            "That’s the essence of backtracking: depth‑first traversal, "
            "recording decisions, and retreating when necessary. "
            "In the next videos we’ll see this pattern in action and learn how to make it efficient.",
            "outro.wav",
        ),
    ]


# ----------------------------
# Main
# ----------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    segments = narration_segments()

    print("\nGenerating audio with Deepgram...\n")

    wav_paths: List[Path] = []
    durations: List[float] = []

    for text, filename in segments:
        out_path = OUTPUT_DIR / filename
        print(f"- Generating {filename}")
        dur = tts_to_wav(text, out_path)
        wav_paths.append(out_path)
        durations.append(dur)
        print(f"  duration: {dur:.2f}s\n")

    final_audio = OUTPUT_DIR / FINAL_AUDIO_NAME
    concat_wavs(wav_paths, final_audio)

    total_duration = wav_duration_seconds(final_audio)

    print("Done.")
    print("Segment durations:", [round(d, 2) for d in durations])
    print(f"{FINAL_AUDIO_NAME} duration: {total_duration:.2f}s")
    print("Audio written to:", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()