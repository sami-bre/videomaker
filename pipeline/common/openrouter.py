import base64
import time

from pipeline.common.http import ApiError, request_with_retry
from pipeline.common.runlog import logged_call

CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(key, model, prompt, *, stage, seed=None):
    """Send one user message and return the reply text. OpenRouter reports the billed cost in `usage.cost`."""
    params = {"prompt": prompt}
    with logged_call(stage, "openrouter", model, params, seed=seed) as record:
        body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if seed is not None:
            body["seed"] = seed
        data = request_with_retry(
            "POST", CHAT_URL, headers={"Authorization": f"Bearer {key}"}, json=body
        ).json()
        if not data.get("choices"):
            raise ApiError(f"no choices in response: {str(data)[:300]}")
        text = (data["choices"][0]["message"].get("content") or "").strip()
        cost = data.get("usage", {}).get("cost")
        record["list_price_usd"] = cost
        record["billed_usd"] = cost or 0.0
        record["output"] = text
    return text


VIDEOS_URL = "https://openrouter.ai/api/v1/videos"
VIDEO_TERMINAL_FAILURES = {"failed", "cancelled", "expired"}


def generate_video(key, model, prompt, first_frame, *, duration, resolution, out_path, poll_timeout_s=900):
    """Image-to-video from a local first-frame image. Returns (out_path, billed USD from `usage.cost`)."""
    headers = {"Authorization": f"Bearer {key}"}
    image_url = "data:image/png;base64," + base64.b64encode(first_frame.read_bytes()).decode()
    body = {
        "model": model,
        "prompt": prompt,
        "frame_images": [{"type": "image_url", "image_url": {"url": image_url}, "frame_type": "first_frame"}],
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": "16:9",
        "generate_audio": False,
    }
    job = request_with_retry("POST", VIDEOS_URL, headers=headers, json=body).json()
    deadline = time.monotonic() + poll_timeout_s
    while time.monotonic() < deadline:
        time.sleep(5)
        status = request_with_retry("GET", f"{VIDEOS_URL}/{job['id']}", headers=headers).json()
        if status["status"] == "completed":
            content = request_with_retry("GET", f"{VIDEOS_URL}/{job['id']}/content", headers=headers, params={"index": 0})
            out_path.write_bytes(content.content)
            return out_path, (status.get("usage") or {}).get("cost")
        if status["status"] in VIDEO_TERMINAL_FAILURES:
            raise ApiError(f"video job {job['id']} {status['status']}: {status.get('error')}")
    raise ApiError(f"video job {job['id']} still running after {poll_timeout_s} s")
