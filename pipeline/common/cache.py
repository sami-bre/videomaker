import hashlib
import json
from pipeline.common.workspace import outputs_dir


def input_hash(inputs):
    """A short, stable hash of everything that affects a stage's output. Key order does not matter."""
    canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def cached_path(stage, name, inputs, suffix):
    """Where the output for these inputs lives, e.g. outputs/narration/s04-3f9a1c2b7d10.wav.

    If the file already exists, the stage can skip the model call. Changing any input
    gives a new hash and so a new file; old files stay for inspection.
    """
    directory = outputs_dir() / stage
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{name}-{input_hash(inputs)}{suffix}"
