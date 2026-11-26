"""Music stage: score candidates from ACE-Step 1.5 on WaveSpeed, one per seed in the
storyboard's `music.seeds`. Listen, then set `music.chosen_seed` (and `why_chosen`).

Run: uv run python -m pipeline.music [path/to/storyboard.json]

The length is the whole film (every shot plus the end card), so one cue covers it.
Candidates are cached by caption, length, seed and model.
"""

import math
import os
import sys

from dotenv import load_dotenv

from pipeline import assemble
from pipeline import storyboard as sb
from pipeline.common import wavespeed
from pipeline.common.cache import cached_path
from pipeline.common.runlog import logged_call

STAGE = "music"
MODEL = "wavespeed-ai/ace-step-1.5"
# From docs/research/external-services.md, checked 2026-11-25.
USD_PER_SECOND = 0.0003
TAIL_S = 2


def film_length_s(storyboard):
    return math.ceil(sum(assemble.shot_lengths(storyboard).values()) + assemble.END_CARD_S + TAIL_S)


def candidate_inputs(storyboard, seed):
    return {"caption": storyboard["music"]["caption"], "duration": film_length_s(storyboard), "seed": seed, "model": MODEL}


def candidate_path(storyboard, seed):
    return cached_path(STAGE, f"seed{seed}", candidate_inputs(storyboard, seed), ".mp3")


def chosen_track(storyboard):
    seed = storyboard.get("music", {}).get("chosen_seed")
    return candidate_path(storyboard, seed) if seed is not None else None


def generate(key, storyboard, seed):
    inputs = candidate_inputs(storyboard, seed)
    out = candidate_path(storyboard, seed)
    cost = round(inputs["duration"] * USD_PER_SECOND, 4)
    with logged_call(STAGE, "wavespeed", MODEL, inputs, seed=seed, list_price_usd=cost, billed_usd=cost) as record:
        body = {"tags": inputs["caption"], "lyrics": "[instrumental]", "duration": inputs["duration"], "seed": seed}
        saved = wavespeed.download(wavespeed.run_task(key, MODEL, body), out.with_suffix(""))
        if saved != out:
            saved.rename(out)
        record["output"] = str(out.relative_to(sb.ROOT))
    return out


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    if "music" not in storyboard:
        raise sb.StoryboardError("storyboard has no `music` cue")
    key = os.environ["WAVESPEED_API_KEY"]
    for seed in storyboard["music"]["seeds"]:
        out = candidate_path(storyboard, seed)
        status = "cached" if out.exists() else "generated"
        if not out.exists():
            generate(key, storyboard, seed)
        print(f"seed {seed}: {status} -> {out.relative_to(sb.ROOT)}")
    chosen = storyboard["music"].get("chosen_seed")
    print(f"music: {film_length_s(storyboard)} s per candidate; chosen seed: {chosen if chosen is not None else 'none yet'}")


if __name__ == "__main__":
    load_dotenv()
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
