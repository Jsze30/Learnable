"""
ai_gen_audio.py

Boilerplate script for generating narration audio using Deepgram TTS.
Designed to be run ONCE before rendering Manim videos.

Pipeline:
1. Define narration segments (text + filename)
2. Generate WAV files via Deepgram
3. Concatenate segments into a single narration.wav
4. Print durations for timing / debugging

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
    Return a list of (text, filename) pairs.

    Edit this function for each video.
    Filenames should end with .wav.
    """
    return [
        (
            "Welcome! In this video we'll explore the idea of backtracking, "
            "a systematic way of trying every possibility until we find a solution.",
            "seg1.wav",
        ),
        (
            "Think of a decision tree where each node represents a partial solution. "
            "We explore one branch depth‑first, building choices step by step.",
            "seg2.wav",
        ),
        (
            "Imagine a tiny recursion fairy walking down a branching maze, "
            "leaving a breadcrumb for the current partial solution. "
            "When she hits a dead end, she lifts the breadcrumb and tries the next corridor.",
            "seg3.wav",
        ),
        (
            "Because we eventually visit every branch, backtracking guarantees that if a solution "
            "exists in a finite tree, we'll find it – or we can stop at the first one.",
            "seg4.wav",
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