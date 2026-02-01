import os
import wave
import contextlib
from pathlib import Path

import requests

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"

def wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        return wf.getnframes() / float(wf.getframerate())

def tts_to_wav(text: str, out_path: Path, model: str = "aura-2-thalia-en") -> float:
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPGRAM_API_KEY env var. Export it first.")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = {"model": model, "encoding": "linear16", "container": "wav"}
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    payload = {"text": text}

    r = requests.post(DEEPGRAM_TTS_URL, params=params, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    return wav_duration_seconds(out_path)

def concat_wavs(wav_paths, out_path: Path):
    """
    Concatenate WAVs (must share sample rate/channels/sample width).
    """
    if not wav_paths:
        raise ValueError("No WAVs to concatenate.")

    with wave.open(str(wav_paths[0]), "rb") as w0:
        params0 = w0.getparams()

    frames_all = []
    for p in wav_paths:
        with wave.open(str(p), "rb") as w:
            if w.getparams()[:4] != params0[:4]:
                raise RuntimeError(f"WAV format mismatch: {p.name} differs from first file.")
            frames_all.append(w.readframes(w.getnframes()))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as out:
        out.setparams(params0)
        for fr in frames_all:
            out.writeframes(fr)

def main():
    sounds_dir = Path("assets/sounds")
    sounds_dir.mkdir(parents=True, exist_ok=True)

    segments = [
        ("Backtracking is a pattern for exploring many possibilities without getting lost. "
         "You build a partial solution, make a choice, and go deeper.", "seg1.wav"),
        ("If you hit a dead end, you undo the last choice and try the next option. "
         "Try. Recurse. Undo. That undo step is the backtrack.", "seg2.wav"),
        ("A great mental model is a maze. At each junction you pick a corridor. "
         "When it fails, you walk back to the last junction and take a different corridor.", "seg3.wav"),
        ("The recursion tree is the map of all those junctions and choices. "
         "Each node is a partial solution. Each edge is a decision you try next.", "seg4.wav"),
        ("And the catch is cost. If you have b choices per step and depth d, "
         "the tree can have about b to the d nodes. That is why backtracking can be exponential.", "seg5.wav"),
    ]

    print("Generating audio segments with Deepgram...\n")

    wav_paths = []
    durations = []
    for text, fname in segments:
        out_path = sounds_dir / fname
        print(f"- {fname}")
        dur = tts_to_wav(text, out_path)
        wav_paths.append(out_path)
        durations.append(dur)
        print(f"  duration: {dur:.2f}s\n")

    narration_path = sounds_dir / "narration.wav"
    concat_wavs(wav_paths, narration_path)

    total = wav_duration_seconds(narration_path)
    print("Done.")
    print("Segment durations:", [round(d, 2) for d in durations])
    print(f"narration.wav duration: {total:.2f}s")
    print("Audio written to:", sounds_dir.resolve())

if __name__ == "__main__":
    main()
