"""Script stage: translate each line's English text into the narration language.

Run: uv run python -m pipeline.script [path/to/storyboard.json]

Only lines with no translation, or whose English changed since they were translated,
are sent to the model. A hand edit of `spoken` is kept as long as `en` is unchanged.
All lines go in one call so the model sees the whole story (speakers, tone, gender).
"""

import json
import sys

import requests

from pipeline import storyboard as sb
from pipeline.common import addis, openrouter
from pipeline.common.http import ApiError
from pipeline.common.workspace import load_keys, require_key

# Chosen by a native speaker (EXPERIMENTS.md E2, E3). Addis AI only covers its own languages.
ADDIS_LANGUAGES = {"am", "om"}
FALLBACK_MODEL = "google/gemini-2.5-flash"
LANGUAGE_NAMES = {"am": "Amharic", "ti": "Tigrinya", "om": "Afaan Oromo", "so": "Somali"}


def lines_needing_translation(storyboard):
    return [
        (f"{shot['id']}-{i}", line)
        for shot in storyboard["shots"]
        for i, line in enumerate(shot["lines"])
        if "spoken" not in line or line.get("spoken_from_en") != line["en"]
    ]


def build_prompt(storyboard, pending):
    language = LANGUAGE_NAMES.get(storyboard["narration_language"], storyboard["narration_language"])
    script = "\n".join(
        f"[{shot['id']}-{i}] {line['speaker']}: {line['en']}"
        for shot in storyboard["shots"]
        for i, line in enumerate(shot["lines"])
    )
    keys = ", ".join(key for key, _ in pending)
    notes = f"- {storyboard['translation_notes']}\n" if storyboard.get("translation_notes") else ""
    return f"""You translate the narration of a short film into natural, spoken {language}.

Film: {storyboard['title']}. {storyboard.get('logline', '')}

Rules:
- Write it the way people really talk, not formal written language. It will be read aloud by a text-to-speech voice.
- Keep each line about as short as the English.
- Get gender and kinship words right for each speaker. Speaker names describe who talks.
- Keep place names recognisable, using their usual {language} names.
{notes}
Full script, for context:
{script}

Translate only these lines: {keys}
Reply with one JSON object mapping each key to its translation, and nothing else."""


def parse_translations(text, expected_keys):
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    translations = json.loads(cleaned)
    missing = set(expected_keys) - set(translations)
    if missing:
        raise ApiError(f"translation is missing keys: {', '.join(sorted(missing))}")
    return {key: translations[key].strip() for key in expected_keys}


def translate(prompt, language, keys):
    """Return (model, translations). Tries Addis AI first, then Gemini 2.5 Flash on OpenRouter."""
    if language in ADDIS_LANGUAGES:
        try:
            reply = addis.chat(require_key("ADDIS_API_KEY"), prompt, target_language=language, stage="script")
            return addis.CHAT_MODEL, parse_translations(reply, keys)
        except (ApiError, requests.RequestException, KeyError, ValueError) as exc:
            print(f"Addis AI failed ({exc}); falling back to {FALLBACK_MODEL}")
    reply = openrouter.chat(require_key("OPENROUTER_API_KEY"), FALLBACK_MODEL, prompt, stage="script")
    return FALLBACK_MODEL, parse_translations(reply, keys)


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    pending = lines_needing_translation(storyboard)
    if not pending:
        print("script: all lines already translated, nothing to do")
        return storyboard

    model, translations = translate(
        build_prompt(storyboard, pending), storyboard["narration_language"], [key for key, _ in pending]
    )
    for key, line in pending:
        line["spoken"] = translations[key]
        line["spoken_from_en"] = line["en"]
        print(f"{key}: {line['spoken']}")
    sb.save(storyboard, path)
    print(f"script: translated {len(pending)} lines with {model}")
    return storyboard


if __name__ == "__main__":
    load_keys()
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
