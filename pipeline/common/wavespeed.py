import time
from pathlib import Path

from pipeline.common.http import ApiError, request_with_retry

BASE_URL = "https://api.wavespeed.ai/api/v3"
TERMINAL_FAILURES = {"failed", "cancelled", "timeout", "deleted"}


def upload(key, path):
    """Upload a local file and return a URL that WaveSpeed models accept as input (kept for 7 days)."""
    data = request_with_retry(
        "POST",
        f"{BASE_URL}/media/uploads",
        headers={"Authorization": f"Bearer {key}"},
        json={"filename": path.name, "size": path.stat().st_size},
    ).json()["data"]
    request_with_retry("PUT", data["upload"]["url"], headers=data["upload"].get("headers", {}), data=path.read_bytes())
    return data["download_url"]


def run_task(key, model_path, body, poll_timeout_s=900):
    """Submit a task, wait for it, and return its first output URL."""
    headers = {"Authorization": f"Bearer {key}"}
    task_id = request_with_retry("POST", f"{BASE_URL}/{model_path}", headers=headers, json=body).json()["data"]["id"]
    deadline = time.monotonic() + poll_timeout_s
    while time.monotonic() < deadline:
        time.sleep(3)
        data = request_with_retry("GET", f"{BASE_URL}/predictions/{task_id}/result", headers=headers).json()["data"]
        if data["status"] == "completed":
            return data["outputs"][0]
        if data["status"] in TERMINAL_FAILURES:
            raise ApiError(f"task {task_id} {data['status']}: {data.get('error')}")
    raise ApiError(f"task {task_id} still running after {poll_timeout_s} s")


def download(url, out_stem):
    """Save `url` next to `out_stem`, keeping the file extension from the URL."""
    out_path = Path(f"{out_stem}{Path(url.split('?')[0]).suffix or '.bin'}")
    out_path.write_bytes(request_with_retry("GET", url).content)
    return out_path
