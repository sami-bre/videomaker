"""Load, validate and save storyboard.json.

Run: uv run python -m pipeline.storyboard [path/to/storyboard.json]
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"
DEFAULT_PATH = ROOT / "storyboard.json"


class StoryboardError(ValueError):
    pass


def validation_errors(storyboard):
    validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    errors = [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(root)'}: {err.message}"
        for err in sorted(validator.iter_errors(storyboard), key=lambda e: list(e.absolute_path))
    ]
    if not errors:
        ids = [shot["id"] for shot in storyboard["shots"]]
        errors += [f"shots: id {i} is used more than once" for i in sorted({i for i in ids if ids.count(i) > 1})]
    if not errors and "voices" in storyboard:
        speakers = {line["speaker"] for shot in storyboard["shots"] for line in shot["lines"]}
        errors += [f"voices: no voice for speaker {s}" for s in sorted(speakers - set(storyboard["voices"]))]
    if not errors:
        known = set(storyboard.get("characters", {}))
        errors += [
            f"shots/{shot['id']}: unknown character {c}"
            for shot in storyboard["shots"]
            for c in shot.get("characters", [])
            if c not in known
        ]
    return errors


def load(path=DEFAULT_PATH):
    path = Path(path)
    try:
        storyboard = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StoryboardError(f"{path} is not valid JSON: {exc}") from exc
    errors = validation_errors(storyboard)
    if errors:
        raise StoryboardError(f"{path} does not match the schema:\n  " + "\n  ".join(errors))
    return storyboard


def save(storyboard, path=DEFAULT_PATH):
    errors = validation_errors(storyboard)
    if errors:
        raise StoryboardError("refusing to save an invalid storyboard:\n  " + "\n  ".join(errors))
    Path(path).write_text(json.dumps(storyboard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def total_duration_s(storyboard):
    return sum(shot["duration_s"] for shot in storyboard["shots"])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    try:
        storyboard = load(path)
    except StoryboardError as exc:
        print(exc)
        return 1
    words = sum(len(line["en"].split()) for shot in storyboard["shots"] for line in shot["lines"])
    print(f"ok: {len(storyboard['shots'])} shots, {total_duration_s(storyboard):g} s planned, {words} English words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
