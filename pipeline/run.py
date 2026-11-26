"""Run the pipeline, storyboard to finished film, in stage order.

Run: uv run python -m pipeline.run [--stages script,narration] [--quality draft|final] [path/to/storyboard.json]
     (or: make film)

Every stage caches its outputs by a hash of the inputs it uses, so a rerun only calls a
model for what changed in storyboard.json; everything else is reused from outputs/.

With --events, each stage start and end is also printed as one `@@{json}` line, which the
web service reads to show progress.
"""

import argparse
import json
import time

from pipeline import film, keyframes, music, narration, script, shots
from pipeline import storyboard as sb
from pipeline.common.workspace import load_keys

STAGES = {
    "script": lambda path, quality: script.run(path),
    "narration": lambda path, quality: narration.run(path),
    "keyframes": lambda path, quality: keyframes.run(path),
    "shots": lambda path, quality: shots.run(path, quality=quality),
    "music": lambda path, quality: music.run(path),
    "film": lambda path, quality: film.run(path),
}
EVENT_PREFIX = "@@"


def emit(events, **event):
    if events:
        print(EVENT_PREFIX + json.dumps(event), flush=True)


def main(path=sb.DEFAULT_PATH, stages=tuple(STAGES), quality="final", events=False):
    load_keys()
    sb.load(path)
    started = time.monotonic()
    for name in stages:
        print(f"\n== {name}", flush=True)
        emit(events, stage=name, status="started")
        stage_start = time.monotonic()
        try:
            STAGES[name](path, quality)
        except Exception as exc:
            emit(events, stage=name, status="failed", error=str(exc))
            raise
        seconds = round(time.monotonic() - stage_start, 1)
        emit(events, stage=name, status="done", seconds=seconds)
        print(f"   ({seconds} s)", flush=True)
    print(f"\ndone in {time.monotonic() - started:.1f} s")


def parse_stages(text):
    names = [s.strip() for s in text.split(",") if s.strip()]
    unknown = [n for n in names if n not in STAGES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown stages {unknown}; choose from {list(STAGES)}")
    return [n for n in STAGES if n in names]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("storyboard", nargs="?", default=sb.DEFAULT_PATH)
    parser.add_argument("--stages", type=parse_stages, default=list(STAGES), help="comma-separated, e.g. script,narration")
    parser.add_argument("--quality", choices=["draft", "final"], default="final", help="shots resolution: draft 480p or final 720p")
    parser.add_argument("--events", action="store_true", help="also print @@{json} progress lines")
    args = parser.parse_args()
    main(args.storyboard, args.stages, args.quality, args.events)
