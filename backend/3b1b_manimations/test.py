from pathlib import Path
from backtracking_video1 import tts_to_wav

tts_to_wav(
    "Test audio",
    Path("assets/sounds/test.wav")
)
print("done")