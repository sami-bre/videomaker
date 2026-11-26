import time

import requests

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
# A provider may ask us to wait minutes (e.g. a used-up daily quota). Past this we give up
# at once, so the caller can fall back to another model instead of hanging.
MAX_RETRY_WAIT_S = 30


class ApiError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def request_with_retry(method, url, *, attempts=4, timeout=120, **kwargs):
    """Send a request, retrying rate limits, server errors and dropped connections with backoff."""
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == attempts:
                raise
            time.sleep(2**attempt)
            continue

        if resp.status_code in RETRYABLE_STATUSES and attempt < attempts:
            retry_after = resp.headers.get("Retry-After", "")
            wait = float(retry_after) if retry_after.isdigit() else 2**attempt
            if wait <= MAX_RETRY_WAIT_S:
                time.sleep(wait)
                continue

        if not resp.ok:
            raise ApiError(f"HTTP {resp.status_code} from {url}: {resp.text[:300]}", status=resp.status_code)
        return resp
