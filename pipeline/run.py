"""Run the whole pipeline, storyboard to finished film, in stage order.

Run: uv run python -m pipeline.run [path/to/storyboard.json]   (or: make film)

Every stage caches its outputs by a hash of the inputs it uses, so a rerun only calls a
model for what changed in storyboard.json; everything else is reused from outputs/.
"""

import sys
import time

from dotenv import load_dotenv

from pipeline import film, keyframes, music, narration, script, shots
from pipeline import storyboard as sb

STAGES = [
    ("script", lambda path: script.run(path)),
    ("narration", lambda path: narration.run(path)),
    ("keyframes", lambda path: keyframes.run(path)),
    ("shots", lambda path: shots.run(path, quality="final")),
    ("music", lambda path: music.run(path)),
    ("film", lambda path: film.run(path)),
]


def main(path=sb.DEFAULT_PATH):
    load_dotenv()
    sb.load(path)
    started = time.monotonic()
    for name, stage in STAGES:
        print(f"\n== {name}")
        stage_start = time.monotonic()
        stage(path)
        print(f"   ({time.monotonic() - stage_start:.1f} s)")
    print(f"\ndone in {time.monotonic() - started:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
