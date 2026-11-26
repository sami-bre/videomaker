import requests

from pipeline.common.http import ApiError, request_with_retry
from pipeline.common.runlog import logged_call

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"

# Each Gemini model has its own rate limits and its own load, so a busy model is
# usually a reason to try the next one rather than to wait.
TEXT_MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
TTS_MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts"]

# USD per token (input, output), from docs/research/external-services.md, checked 2026-11-25.
LIST_PRICES = {
    "gemini-3.8-flash": (0.75 / 1e6, 3.75 / 1e6),
    "gemini-3.5-flash-lite": (0.30 / 1e6, 2.50 / 1e6),
    "gemini-3.8-flash-tts": (0.50 / 1e6, 9.00 / 1e6),
    "gemini-3.8-flash-lite-tts": (0.50 / 1e6, 6.00 / 1e6),
}

FALLBACK_STATUSES = {429, 503}


def list_price(model, usage):
    if model not in LIST_PRICES or not usage:
        return None
    price_in, price_out = LIST_PRICES[model]
    return round(usage.get("total_input_tokens", 0) * price_in + usage.get("total_output_tokens", 0) * price_out, 6)


def output_contents(data, content_type):
    return [
        content
        for step in data.get("steps", [])
        if step.get("type") == "model_output"
        for content in step.get("content", [])
        if content.get("type") == content_type
    ]


def interact_with_fallback(key, models, body, *, stage, params, handle, seed=None):
    """Call the Interactions API with the first model that is not overloaded or over quota.

    `handle` turns the response JSON into the value to return; it runs inside the
    logged call, so its result is what runs.jsonl records as the output.
    """
    last_error = None
    for model in models:
        try:
            with logged_call(stage, "gemini", model, params, seed=seed) as record:
                data = request_with_retry(
                    "POST",
                    INTERACTIONS_URL,
                    headers={"x-goog-api-key": key},
                    json={"model": model, **body},
                    attempts=2,
                    timeout=90,
                ).json()
                value = handle(data)
                record["list_price_usd"] = list_price(model, data.get("usage"))
                record["output"] = str(value)
            return model, value
        except ApiError as exc:
            if exc.status not in FALLBACK_STATUSES:
                raise
            last_error = exc
        except requests.Timeout as exc:
            last_error = exc
    raise ApiError(f"all models unavailable ({', '.join(models)}); last error: {last_error}")
