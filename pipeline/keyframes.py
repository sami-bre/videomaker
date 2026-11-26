"""Keyframes stage: a reference image per character, then one keyframe per shot
conditioned on the references of the characters in it.

Run: uv run python -m pipeline.keyframes [path/to/storyboard.json]

A keyframe's cache key includes the bytes of its reference images, so regenerating a
character's reference regenerates every keyframe that shows that character.
"""

import hashlib
import subprocess
import sys

from pipeline import storyboard as sb
from pipeline.common import cloudflare
from pipeline.common.cache import cached_path
from pipeline.common.workspace import load_keys, relative, require_key

STAGE = "keyframes"
KEYFRAME_SIZE = (1280, 720)
REFERENCE_SIZE = (1024, 1024)
# Cloudflare requires each reference image to be smaller than 512x512.
REFERENCE_INPUT_PX = 496


def reference_prompt(storyboard, character_id):
    description = storyboard["characters"][character_id]["description"]
    return (
        f"{storyboard['style']} Character reference: a single full-body view of {description}, "
        "standing, facing the viewer, neutral friendly pose, plain light beige background, centred."
    )


def reference_inputs(storyboard, character_id):
    character = storyboard["characters"][character_id]
    return {"prompt": reference_prompt(storyboard, character_id), "size": REFERENCE_SIZE, "seed": character.get("seed", 0), "model": cloudflare.IMAGE_MODEL}


def reference_path(storyboard, character_id):
    return cached_path(STAGE, f"ref-{character_id}", reference_inputs(storyboard, character_id), ".png")


def reference_input_path(storyboard, character_id):
    """The small copy of a reference that is sent to the model."""
    return reference_path(storyboard, character_id).with_suffix(".small.png")


def keyframe_prompt(storyboard, shot):
    characters = shot.get("characters", [])
    cast = " ".join(
        f"Character from reference image {n}: {storyboard['characters'][c]['description']}; keep this exact look."
        for n, c in enumerate(characters)
    )
    # References tend to pull their standing pose into every shot, so the action goes first
    # and the references are limited to looks.
    pose_rule = (
        "Use the reference images only for how each character looks (face, hair, clothes); "
        "draw their pose and action exactly as described here."
        if characters
        else ""
    )
    return " ".join(part for part in (shot["image_prompt"], cast, pose_rule, storyboard["style"]) if part)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def keyframe_inputs(storyboard, shot):
    return {
        "prompt": keyframe_prompt(storyboard, shot),
        "size": KEYFRAME_SIZE,
        "seed": shot.get("seed", 0),
        "model": cloudflare.IMAGE_MODEL,
        "references": [file_hash(reference_input_path(storyboard, c)) for c in shot.get("characters", [])],
    }


def keyframe_path(storyboard, shot):
    return cached_path(STAGE, shot["id"], keyframe_inputs(storyboard, shot), ".png")


def shrink(src, dst, px=REFERENCE_INPUT_PX):
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"scale={px}:{px}", str(dst)],
        check=True,
    )


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    missing = [s["id"] for s in storyboard["shots"] if "image_prompt" not in s]
    if "style" not in storyboard or missing:
        raise sb.StoryboardError(f"keyframes need a top-level `style` and an `image_prompt` on every shot (missing: {missing})")
    made = skipped = 0

    used = sorted({c for shot in storyboard["shots"] for c in shot.get("characters", [])})
    for character_id in used:
        out = reference_path(storyboard, character_id)
        if out.exists():
            skipped += 1
        else:
            width, height = REFERENCE_SIZE
            cloudflare.generate_image(
                require_key("CLOUDFLARE_ACCOUNT_ID"), require_key("CLOUDFLARE_API_TOKEN"), reference_prompt(storyboard, character_id),
                width=width, height=height, seed=storyboard["characters"][character_id].get("seed", 0),
                stage=STAGE, out_path=out,
            )
            made += 1
            print(f"reference {character_id}: {relative(out)}")
        if not reference_input_path(storyboard, character_id).exists():
            shrink(out, reference_input_path(storyboard, character_id))

    for shot in storyboard["shots"]:
        out = keyframe_path(storyboard, shot)
        if out.exists():
            skipped += 1
            continue
        width, height = KEYFRAME_SIZE
        cloudflare.generate_image(
            require_key("CLOUDFLARE_ACCOUNT_ID"), require_key("CLOUDFLARE_API_TOKEN"), keyframe_prompt(storyboard, shot),
            width=width, height=height, seed=shot.get("seed", 0),
            references=[reference_input_path(storyboard, c) for c in shot.get("characters", [])],
            stage=STAGE, out_path=out,
        )
        made += 1
        print(f"keyframe {shot['id']}: {relative(out)}")
    print(f"keyframes: {made} generated, {skipped} cached")


if __name__ == "__main__":
    load_keys()
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
