"""Before a run: how many outputs each stage would make (vs reuse from the cache), what that
costs at list price, and which API keys those calls need.

Run: uv run python -m pipeline.estimate [--stages shots,music] [--quality draft|final] [path/to/storyboard.json]

An output whose inputs are not made yet (a clip whose keyframe does not exist, a voice line
not translated yet) counts as "to make", because its hash cannot be known until then.
"""

import argparse
import json

from pipeline import keyframes, music, narration, run, script, shots
from pipeline import storyboard as sb

UNKNOWN_YET = (FileNotFoundError, KeyError, sb.StoryboardError)


def exists(make_path):
    try:
        path = make_path()
    except UNKNOWN_YET:
        return False
    return path is not None and path.exists()


def count(checks):
    cached = sum(1 for check in checks if exists(check))
    return len(checks) - cached, cached


def list_lines(storyboard):
    return [(shot, i) for shot in storyboard["shots"] for i, _ in enumerate(shot["lines"])]


def script_estimate(storyboard, quality):
    to_make = len(script.lines_needing_translation(storyboard))
    key = ["ADDIS_API_KEY"] if storyboard["narration_language"] in script.ADDIS_LANGUAGES else ["OPENROUTER_API_KEY"]
    return to_make, len(list_lines(storyboard)) - to_make, 0.0, key


def narration_estimate(storyboard, quality):
    to_make, cached = count([lambda s=s, i=i: narration.line_audio_path(storyboard, s, i) for s, i in list_lines(storyboard)])
    return to_make, cached, 0.0, ["GEMINI_API_KEY"]


def keyframes_estimate(storyboard, quality):
    used = sorted({c for shot in storyboard["shots"] for c in shot.get("characters", [])})
    checks = [lambda c=c: keyframes.reference_path(storyboard, c) for c in used]
    checks += [lambda s=s: keyframes.keyframe_path(storyboard, s) for s in storyboard["shots"]]
    to_make, cached = count(checks)
    return to_make, cached, 0.0, ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"]


def shots_estimate(storyboard, quality):
    engine = storyboard.get("video_engine", "wan")
    _, _, usd_per_s, usd_per_image = shots.ENGINES[engine][quality]
    to_make = [s for s in storyboard["shots"] if not exists(lambda s=s: shots.clip_path(storyboard, s, quality, engine))]
    usd = sum(usd_per_s * s.get("clip_s", 5) + usd_per_image for s in to_make)
    key = ["OPENROUTER_API_KEY"] if engine == "grok" else ["WAVESPEED_API_KEY"]
    return len(to_make), len(storyboard["shots"]) - len(to_make), usd, key


def music_estimate(storyboard, quality):
    if "music" not in storyboard:
        return 0, 0, 0.0, []
    seeds = storyboard["music"]["seeds"]
    to_make, cached = count([lambda seed=seed: music.candidate_path(storyboard, seed) for seed in seeds])
    try:
        length_s = music.film_length_s(storyboard)
    except UNKNOWN_YET:
        length_s = sb.total_duration_s(storyboard)
    return to_make, cached, to_make * length_s * music.USD_PER_SECOND, ["WAVESPEED_API_KEY"]


def film_estimate(storyboard, quality):
    return 0, 0, 0.0, []


def plural(count, word):
    return f"{count} {word}" + ("" if count == 1 else "s")


def missing_translations(storyboard):
    count = sum(1 for shot in storyboard["shots"] for line in shot["lines"] if "spoken" not in line)
    return count and f"{plural(count, 'line')} not translated yet"


def missing_voices(storyboard):
    count = sum(1 for s, i in list_lines(storyboard) if not exists(lambda s=s, i=i: narration.line_audio_path(storyboard, s, i)))
    return count and f"{plural(count, 'voice line')} missing"


def missing_keyframes(storyboard):
    count = sum(1 for s in storyboard["shots"] if not exists(lambda s=s: keyframes.keyframe_path(storyboard, s)))
    return count and f"{plural(count, 'shot')} without a picture"


def missing_clips(storyboard):
    count = sum(1 for s in storyboard["shots"] if not exists(lambda s=s: shots.best_clip(storyboard, s)))
    return count and f"{plural(count, 'shot')} without a clip"


def missing_music(storyboard):
    if music.chosen_seed(storyboard) is None:
        return "no music in the storyboard"
    return not exists(lambda: music.chosen_track(storyboard)) and "the film's music is not made yet"


# For each stage: (the earlier stage that provides it, a check returning what is missing or a falsy value).
NEEDS = {
    "script": [],
    "narration": [("script", missing_translations)],
    "keyframes": [],
    "shots": [("keyframes", missing_keyframes)],
    "music": [("narration", missing_voices)],
    "film": [("narration", missing_voices), ("shots", missing_clips), ("music", missing_music)],
}


def waiting_for(storyboard, stage, coming=()):
    """What `stage` needs from earlier stages that is not made yet, e.g. ["Voice: 1 voice line missing"].

    Needs met by a stage in `coming` (earlier in the same run) are left out. Checking up
    front means a run is refused with a plain reason instead of failing partway.
    """
    problems = []
    for provider, check in NEEDS[stage]:
        if provider not in coming:
            missing = check(storyboard)
            if missing:
                problems.append(f"{STEP_NAMES[provider]}: {missing}")
    return problems


STEP_NAMES = {"script": "Translate", "narration": "Voice", "keyframes": "Pictures", "shots": "Motion", "music": "Music", "film": "Film"}

ESTIMATORS = {
    "script": script_estimate,
    "narration": narration_estimate,
    "keyframes": keyframes_estimate,
    "shots": shots_estimate,
    "music": music_estimate,
    "film": film_estimate,
}


def estimate(storyboard, stages=tuple(run.STAGES), quality="final"):
    """Per stage: {to_make, cached, est_usd, needs_keys}. Keys are listed only when there is something to make."""
    result = {}
    for name in stages:
        to_make, cached, usd, keys = ESTIMATORS[name](storyboard, quality)
        result[name] = {
            "to_make": to_make, "cached": cached, "est_usd": round(usd, 4),
            "needs_keys": keys if to_make else [], "waiting_for": waiting_for(storyboard, name),
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("storyboard", nargs="?", default=sb.DEFAULT_PATH)
    parser.add_argument("--stages", type=run.parse_stages, default=list(run.STAGES))
    parser.add_argument("--quality", choices=["draft", "final"], default="final")
    args = parser.parse_args()
    print(json.dumps(estimate(sb.load(args.storyboard), args.stages, args.quality), indent=2))
