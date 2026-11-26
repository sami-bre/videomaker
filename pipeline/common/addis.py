from pipeline.common.http import ApiError, request_with_retry
from pipeline.common.runlog import logged_call

BASE_URL = "https://api.addisassistant.com/api/v1"
CHAT_MODEL = "Addis-፩-አሌፍ"


def _post(key, path, body):
    return request_with_retry("POST", f"{BASE_URL}/{path}", headers={"x-api-key": key}, json=body).json()


def chat(key, prompt, *, target_language, stage, temperature=0.7):
    """Addis AI's own LLM. Billed in ETB per token, so cost is logged as token counts, not USD."""
    params = {"prompt": prompt, "target_language": target_language, "temperature": temperature}
    with logged_call(stage, "addis", CHAT_MODEL, params) as record:
        data = _post(
            key,
            "chat_generate",
            {"prompt": prompt, "target_language": target_language, "generation_config": {"temperature": temperature}},
        )
        # The live API wraps the reply in {"status", "data": {...}}; the docs show it unwrapped.
        data = data.get("data", data)
        if "response_text" not in data:
            raise ApiError(f"no response_text: {str(data)[:300]}")
        record["usage"] = data.get("usage_metadata")
        record["output"] = data["response_text"]
    return data["response_text"]


def translate(key, text, *, source_language, target_language, stage):
    params = {"text": text, "source_language": source_language, "target_language": target_language}
    with logged_call(stage, "addis", "addis-translate", params) as record:
        data = _post(key, "translate", params)
        if data.get("status") != "success":
            raise ApiError(f"translation failed: {str(data)[:300]}")
        record["usage"] = data["data"].get("usage_metadata")
        record["output"] = data["data"]["translation"]
    return data["data"]["translation"]
