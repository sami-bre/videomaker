import base64
import math

from pipeline.common.http import ApiError, request_with_retry
from pipeline.common.runlog import logged_call

IMAGE_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
# List prices from docs/research/external-services.md, checked 2026-11-25. The free daily
# allowance covers our volume, so nothing is billed.
USD_PER_OUTPUT_TILE = 0.000287
USD_PER_INPUT_TILE = 0.000059
MAX_REFERENCES = 4


def tiles(width, height):
    return math.ceil(width / 512) * math.ceil(height / 512)


def generate_image(account_id, token, prompt, *, width, height, seed, references=(), stage, out_path):
    """Text-to-image with up to 4 reference images (each must be under 512x512). Writes a PNG."""
    if len(references) > MAX_REFERENCES:
        raise ValueError(f"at most {MAX_REFERENCES} reference images, got {len(references)}")
    params = {"prompt": prompt, "width": width, "height": height, "references": [str(p) for p in references]}
    list_price = tiles(width, height) * USD_PER_OUTPUT_TILE + len(references) * USD_PER_INPUT_TILE
    with logged_call(stage, "cloudflare", IMAGE_MODEL, params, seed=seed, list_price_usd=round(list_price, 6)) as record:
        fields = {"prompt": (None, prompt), "width": (None, str(width)), "height": (None, str(height)), "seed": (None, str(seed))}
        for n, path in enumerate(references):
            fields[f"input_image_{n}"] = (path.name, path.read_bytes(), "image/png")
        data = request_with_retry(
            "POST",
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{IMAGE_MODEL}",
            headers={"Authorization": f"Bearer {token}"},
            files=fields,
        ).json()
        image = data.get("result", data).get("image")
        if not image:
            raise ApiError(f"no image in response: {str(data)[:300]}")
        out_path.write_bytes(base64.b64decode(image))
        record["output"] = str(out_path)
    return out_path
