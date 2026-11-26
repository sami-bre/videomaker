"""Shots stage: animate each keyframe with an image-to-video engine.

Run: uv run python -m pipeline.shots [--final] [--engine wan|grok] [--only s04,s07] [path/to/storyboard.json]

Engines: Wan 2.2 on WaveSpeed, or Grok Imagine 1.5 Lite on OpenRouter. The storyboard's
`video_engine` picks which engine's clips go into the film; --engine only chooses what to
generate, so you can render a comparison without switching. Drafts are 480p; --final
renders 720p. Each clip is cached by a hash of its keyframe's bytes, motion prompt, length,
seed and model. If a call fails, the shot falls back to a slow Ken Burns push-in on the
keyframe, so the film always has a picture for every shot.
"""

import argparse
import hashlib
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

import math

from pipeline import assemble, keyframes
from pipeline import storyboard as sb
from pipeline.common import openrouter, wavespeed
from pipeline.common.cache import cached_path
from pipeline.common.runlog import logged_call

STAGE = "shots"
# (model, resolution, USD per output second, USD per input image). Wan's prices are from
# docs/research/external-services.md (5 s listed; 8 s assumed to scale); Grok's from
# OpenRouter's /api/v1/videos/models, checked 2026-11-26. Grok reports the real cost back.
ENGINES = {
    "wan": {
        "draft": ("wavespeed-ai/wan-2.2/i2v-480p-ultra-fast", None, 0.01, 0.0),
        "final": ("wavespeed-ai/wan-2.2/i2v-720p-ultra-fast", None, 0.02, 0.0),
    },
    "grok": {
        "draft": ("x-ai/grok-imagine-video-1.5-lite", "480p", 0.02, 0.01),
        "final": ("x-ai/grok-imagine-video-1.5-lite", "720p", 0.03, 0.01),
    },
}
KEN_BURNS_SIZE, KEN_BURNS_FPS = (1280, 720), 24
ENGINE_CLIP_LENGTHS = {"wan": {5, 8}, "grok": set(range(1, 16))}
# WaveSpeed returned HTTP 429 "Concurrency" with 4 jobs at once on a new account.
PARALLEL_JOBS = 2


def motion_prompt(storyboard, shot):
    return " ".join(part for part in (shot["motion_prompt"], storyboard.get("motion_style", "")) if part)


def clip_inputs(storyboard, shot, quality, engine):
    model, resolution, _, _ = ENGINES[engine][quality]
    keyframe = keyframes.keyframe_path(storyboard, shot)
    inputs = {
        "keyframe": hashlib.sha256(keyframe.read_bytes()).hexdigest()[:12],
        "motion_prompt": motion_prompt(storyboard, shot),
        "clip_s": shot.get("clip_s", 5),
        "seed": shot.get("seed", 0),
        "model": model,
    }
    if resolution:
        inputs["resolution"] = resolution
    return inputs


def clip_path(storyboard, shot, quality, engine):
    return cached_path(STAGE, f"{shot['id']}-{engine}-{quality}", clip_inputs(storyboard, shot, quality, engine), ".mp4")


def fallback_path(storyboard, shot, quality, engine):
    return clip_path(storyboard, shot, quality, engine).with_suffix(".kenburns.mp4")


def best_clip(storyboard, shot):
    """The clip assembly should use, from the storyboard's engine: final over draft, real clip
    over Ken Burns. None if nothing exists yet."""
    engine = storyboard.get("video_engine", "wan")
    for quality in ("final", "draft"):
        for path in (clip_path(storyboard, shot, quality, engine), fallback_path(storyboard, shot, quality, engine)):
            if path.exists():
                return path
    return None


def ken_burns(keyframe, seconds, out_path):
    width, height = KEN_BURNS_SIZE
    frames = round(seconds * KEN_BURNS_FPS)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(keyframe),
         "-vf", f"scale={width * 2}:-2,zoompan=z='min(zoom+0.0007,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={KEN_BURNS_FPS}",
         "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)],
        check=True,
    )


def generate(storyboard, engine, model, resolution, shot, inputs, out):
    """Make one clip with the given engine. Returns the billed USD if the provider reports it."""
    keyframe = keyframes.keyframe_path(storyboard, shot)
    if engine == "wan":
        key = os.environ["WAVESPEED_API_KEY"]
        body = {"image": wavespeed.upload(key, keyframe), "prompt": inputs["motion_prompt"], "duration": inputs["clip_s"], "seed": inputs["seed"]}
        wavespeed.download(wavespeed.run_task(key, model, body), out.with_suffix("")).rename(out)
        return None
    _, cost = openrouter.generate_video(
        os.environ["OPENROUTER_API_KEY"], model, inputs["motion_prompt"], keyframe,
        duration=inputs["clip_s"], resolution=resolution, out_path=out,
    )
    return cost


def animate(storyboard, shot, quality, engine):
    model, resolution, usd_per_s, usd_per_image = ENGINES[engine][quality]
    inputs = clip_inputs(storyboard, shot, quality, engine)
    estimate = round(usd_per_s * inputs["clip_s"] + usd_per_image, 4)
    out = clip_path(storyboard, shot, quality, engine)
    provider = "wavespeed" if engine == "wan" else "openrouter"
    try:
        with logged_call(STAGE, provider, model, inputs, seed=inputs["seed"], list_price_usd=estimate, billed_usd=estimate) as record:
            billed = generate(storyboard, engine, model, resolution, shot, inputs, out)
            if billed is not None:
                record["billed_usd"] = record["list_price_usd"] = billed
            record["output"] = str(out.relative_to(sb.ROOT))
        return f"{shot['id']}: {engine} {quality} -> {out.name}"
    except Exception as exc:
        fallback = fallback_path(storyboard, shot, quality, engine)
        ken_burns(keyframes.keyframe_path(storyboard, shot), inputs["clip_s"], fallback)
        return f"{shot['id']}: {engine} failed ({str(exc)[:120]}); used Ken Burns -> {fallback.name}"


def length_problems(shots, engine, shot_lengths):
    """Reasons not to render: a clip length the engine can't make, or a clip too short to
    cover its shot's narration even when slowed down. Checked before spending money."""
    problems = []
    for shot in shots:
        clip_s = shot.get("clip_s", 5)
        if clip_s not in ENGINE_CLIP_LENGTHS[engine]:
            problems.append(f"{shot['id']}: {engine} cannot make a {clip_s} s clip (allowed: {sorted(ENGINE_CLIP_LENGTHS[engine])})")
            continue
        shot_s = shot_lengths.get(shot["id"])
        if shot_s and assemble.fit_clip(clip_s, shot_s)[0] == "too_short":
            problems.append(f"{shot['id']}: clip_s {clip_s} is too short for {shot_s:.1f} s of narration; set clip_s to at least {math.ceil(shot_s * assemble.MIN_CLIP_SPEED)} (ideally {math.ceil(shot_s)})")
    return problems


def run(path=sb.DEFAULT_PATH, quality="draft", only=None, engine=None):
    storyboard = sb.load(path)
    engine = engine or storyboard.get("video_engine", "wan")
    shots = [s for s in storyboard["shots"] if not only or s["id"] in only]
    missing = [s["id"] for s in shots if "motion_prompt" not in s or not keyframes.keyframe_path(storyboard, s).exists()]
    if missing:
        raise sb.StoryboardError(f"shots {missing} need a `motion_prompt` and a keyframe; run pipeline.keyframes first")

    try:
        lengths = assemble.shot_lengths(storyboard)
    except sb.StoryboardError:
        print("shots: no narration yet, so clip lengths are not checked against it")
        lengths = {}
    problems = length_problems(shots, engine, lengths)
    if problems:
        raise sb.StoryboardError("not rendering, fix these first:\n  " + "\n  ".join(problems))

    todo = [s for s in shots if not clip_path(storyboard, s, quality, engine).exists()]
    print(f"shots: {len(shots) - len(todo)} cached, {len(todo)} to generate with {engine} at {quality}")
    with ThreadPoolExecutor(PARALLEL_JOBS) as pool:
        for message in pool.map(lambda s: animate(storyboard, s, quality, engine), todo):
            print(message)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("storyboard", nargs="?", default=sb.DEFAULT_PATH)
    parser.add_argument("--final", action="store_true", help="render 720p instead of 480p drafts")
    parser.add_argument("--engine", choices=sorted(ENGINES), help="engine to generate with (default: the storyboard's video_engine)")
    parser.add_argument("--only", help="comma-separated shot ids, e.g. s04,s07")
    args = parser.parse_args()
    run(args.storyboard, "final" if args.final else "draft", set(args.only.split(",")) if args.only else None, args.engine)
