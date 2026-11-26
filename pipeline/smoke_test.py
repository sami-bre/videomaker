"""Call each provider once with a tiny job and log every call to runs.jsonl.

Run: uv run python -m pipeline.smoke_test [text] [narration] [keyframe] [video] [music]
With no names it runs every check. Providers whose keys are missing from .env are skipped.
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from pipeline.common import gemini, wavespeed
from pipeline.common.http import ApiError, request_with_retry
from pipeline.common.runlog import logged_call

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "smoke"
SEED = 42

# List prices from docs/research/external-services.md, checked 2026-11-25.
CLOUDFLARE_KLEIN_USD_PER_512_TILE = 0.000287
WAN_480P_USD_PER_5S_CLIP = 0.05
ACE_STEP_USD_PER_SECOND = 0.0003


class Skipped(Exception):
    pass


def require_env(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise Skipped(f"missing {', '.join(missing)} in .env")
    return [os.environ[n] for n in names]


def gemini_text():
    (key,) = require_env("GEMINI_API_KEY")
    prompt = "Translate into Amharic, reply with the translation only: My grandmother walked to the market every Saturday."
    out_path = OUT_DIR / "translation.txt"

    def handle(data):
        parts = gemini.output_contents(data, "text")
        if not parts:
            raise ApiError(f"no text in response: {str(data)[:300]}")
        text = parts[-1]["text"].strip()
        out_path.write_text(text + "\n", encoding="utf-8")
        return text

    body = {"input": [{"type": "user_input", "content": [{"type": "text", "text": prompt}]}]}
    model, text = gemini.interact_with_fallback(
        key, gemini.TEXT_MODELS, body, stage="smoke", params={"prompt": prompt}, handle=handle
    )
    return f"{model}: {text}"


def gemini_tts():
    (key,) = require_env("GEMINI_API_KEY")
    line = "ሰላም። ይህ የድምፅ ሙከራ ነው።"
    params = {"text": line, "voice": "Kore", "style": "calm, warm, unhurried"}
    out_path = OUT_DIR / "narration.wav"

    def handle(data):
        audio = gemini.output_contents(data, "audio")
        if not audio:
            raise ApiError(f"no audio in response: {str(data)[:300]}")
        out_path.write_bytes(base64.b64decode(audio[-1]["data"]))
        return out_path.relative_to(OUT_DIR.parents[1])

    body = {
        "input": [
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": line,
                        "annotations": [{"type": "speech_metadata", "style": params["style"]}],
                    }
                ],
            }
        ],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": params["voice"]}]},
    }
    model, path = gemini.interact_with_fallback(
        key, gemini.TTS_MODELS, body, stage="smoke", params=params, handle=handle
    )
    return f"{model}: {path}"


def cloudflare_keyframe():
    account_id, token = require_env("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN")
    model = "@cf/black-forest-labs/flux-2-klein-4b"
    params = {
        "prompt": "An elderly Ethiopian woman in a white netela walking along a dirt road to a market at golden hour, warm grainy film look",
        "width": 512,
        "height": 512,
    }
    out_path = OUT_DIR / "keyframe.png"
    with logged_call(
        "smoke", "cloudflare", model, params, seed=SEED, list_price_usd=CLOUDFLARE_KLEIN_USD_PER_512_TILE
    ) as record:
        resp = request_with_retry(
            "POST",
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
            headers={"Authorization": f"Bearer {token}"},
            files={k: (None, str(v)) for k, v in {**params, "seed": SEED}.items()},
        )
        data = resp.json()
        image_b64 = data.get("result", data)["image"]
        out_path.write_bytes(base64.b64decode(image_b64))
        record["output"] = str(out_path.relative_to(OUT_DIR.parents[1]))
    return out_path


def wavespeed_video(keyframe_path):
    (key,) = require_env("WAVESPEED_API_KEY")
    if keyframe_path is None:
        raise Skipped("needs the Cloudflare keyframe")
    model = "wavespeed-ai/wan-2.2/i2v-480p-ultra-fast"
    params = {"prompt": "She walks slowly forward, the camera tracks gently beside her, dust in the warm light", "duration": 5}
    with logged_call(
        "smoke", "wavespeed", model, params, seed=SEED,
        list_price_usd=WAN_480P_USD_PER_5S_CLIP, billed_usd=WAN_480P_USD_PER_5S_CLIP,
    ) as record:
        image_url = wavespeed.upload(key, keyframe_path)
        output_url = wavespeed.run_task(key, model, {**params, "image": image_url, "seed": SEED})
        out_path = wavespeed.download(output_url, OUT_DIR / "clip")
        record["output"] = str(out_path.relative_to(OUT_DIR.parents[1]))
    return out_path


def wavespeed_music():
    (key,) = require_env("WAVESPEED_API_KEY")
    model = "wavespeed-ai/ace-step-1.5"
    params = {"tags": "ambient, soft strings, krar, warm, slow, gentle", "lyrics": "[instrumental]", "duration": 10}
    cost = round(params["duration"] * ACE_STEP_USD_PER_SECOND, 6)
    with logged_call("smoke", "wavespeed", model, params, seed=SEED, list_price_usd=cost, billed_usd=cost) as record:
        output_url = wavespeed.run_task(key, model, {**params, "seed": SEED})
        out_path = wavespeed.download(output_url, OUT_DIR / "music")
        record["output"] = str(out_path.relative_to(OUT_DIR.parents[1]))
    return out_path


def main():
    load_dotenv()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    selected = set(sys.argv[1:])

    def run(name, fn, *args):
        if selected and name.split()[0] not in selected:
            return None
        start = time.monotonic()
        try:
            value = fn(*args)
            results.append((name, "ok", f"{time.monotonic() - start:.1f}s", str(value)[:70]))
            return value
        except Skipped as exc:
            results.append((name, "skipped", "-", str(exc)))
        except Exception as exc:
            results.append((name, "FAILED", f"{time.monotonic() - start:.1f}s", f"{type(exc).__name__}: {exc}"[:200]))
        return None

    run("text (Gemini)", gemini_text)
    run("narration (Gemini TTS)", gemini_tts)
    keyframe = run("keyframe (Cloudflare FLUX.2 klein)", cloudflare_keyframe)
    run("video (WaveSpeed Wan 2.2 480p)", wavespeed_video, keyframe)
    run("music (WaveSpeed ACE-Step 1.5)", wavespeed_music)

    for name, status, latency, detail in results:
        print(f"{status:8} {latency:>7}  {name:36} {detail}")
    return 1 if any(status == "FAILED" for _, status, _, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
