import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

RUNS_FILE = Path(__file__).resolve().parents[2] / "runs.jsonl"


@contextmanager
def logged_call(stage, provider, model, params, seed=None, list_price_usd=None, billed_usd=0.0):
    """Append one line to runs.jsonl per model call, whether it succeeds or fails.

    The caller may fill in record["output"] and adjust the cost fields inside the block.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": stage,
        "provider": provider,
        "model": model,
        "params": params,
        "seed": seed,
        "list_price_usd": list_price_usd,
        "billed_usd": billed_usd,
        "status": None,
        "error": None,
        "output": None,
    }
    start = time.monotonic()
    try:
        yield record
        record["status"] = "ok"
    except Exception as exc:
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"[:500]
        record["billed_usd"] = 0.0
        raise
    finally:
        record["latency_s"] = round(time.monotonic() - start, 3)
        with RUNS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def models_by_output_name():
    """Map each output file name to the model whose successful call wrote it, from runs.jsonl."""
    made_by = {}
    if RUNS_FILE.exists():
        for line in RUNS_FILE.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("status") == "ok" and isinstance(record.get("output"), str) and record["output"].startswith(("outputs/", "/")):
                made_by[Path(record["output"]).name] = record["model"]
    return made_by
