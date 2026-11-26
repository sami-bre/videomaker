"""Music stage: score candidates from ACE-Step 1.5 on WaveSpeed, one per seed in the
storyboard's `music.seeds`. Listen, then set `music.chosen_seed` (and `why_chosen`). Until
you do, the film uses the first seed's candidate, so a first full run still ends in a film.

Run: uv run python -m pipeline.music [path/to/storyboard.json]

The length is the whole film (every shot plus the end card), so one cue covers it.
Candidates are cached by caption, length, seed and model.
"""

import math
import sys

from pipeline import assemble
from pipeline import storyboard as sb
from pipeline.common import wavespeed
from pipeline.common.cache import cached_path
from pipeline.common.runlog import logged_call
from pipeline.common.workspace import load_keys, relative, require_key

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


def chosen_seed(storyboard):
    cue = storyboard.get("music", {})
    return cue.get("chosen_seed", cue["seeds"][0] if cue.get("seeds") else None)


def chosen_track(storyboard):
    seed = chosen_seed(storyboard)
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
        record["output"] = str(relative(out))
    return out


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    if "music" not in storyboard:
        raise sb.StoryboardError("storyboard has no `music` cue")
    for seed in storyboard["music"]["seeds"]:
        out = candidate_path(storyboard, seed)
        status = "cached" if out.exists() else "generated"
        if not out.exists():
            generate(require_key("WAVESPEED_API_KEY"), storyboard, seed)
        print(f"seed {seed}: {status} -> {relative(out)}")
    chosen = "" if "chosen_seed" in storyboard["music"] else " (first seed until you choose one)"
    print(f"music: {film_length_s(storyboard)} s per candidate; film uses seed {chosen_seed(storyboard)}{chosen}")


if __name__ == "__main__":
    load_keys()
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
