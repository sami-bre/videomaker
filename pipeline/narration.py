"""Narration stage: one TTS audio file per spoken line.

Run: uv run python -m pipeline.narration [path/to/storyboard.json]

Each file is named by a hash of the text, voice and style, so changing one line
regenerates only that line. Lines without a `spoken` translation are an error:
run the script stage first.
"""

import base64
import os
import sys
import wave

from dotenv import load_dotenv

from pipeline import storyboard as sb
from pipeline.common import gemini
from pipeline.common.cache import cached_path
from pipeline.common.http import ApiError

STAGE = "narration"


def line_inputs(storyboard, line):
    voice = storyboard["voices"][line["speaker"]]
    return {"text": line["spoken"], "voice": voice["voice"], "style": voice.get("style", ""), "language": storyboard["narration_language"]}


def line_audio_path(storyboard, shot, index):
    return cached_path(STAGE, f"{shot['id']}-{index}", line_inputs(storyboard, shot["lines"][index]), ".wav")


def wav_duration_s(path):
    with wave.open(str(path)) as f:
        return f.getnframes() / f.getframerate()


def synthesize(key, inputs, out_path):
    body = {
        "input": [
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": inputs["text"],
                        "annotations": [{"type": "speech_metadata", "style": inputs["style"]}],
                    }
                ],
            }
        ],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": inputs["voice"]}]},
    }

    def handle(data):
        audio = gemini.output_contents(data, "audio")
        if not audio:
            raise ApiError(f"no audio in response: {str(data)[:300]}")
        out_path.write_bytes(base64.b64decode(audio[-1]["data"]))
        return out_path.relative_to(sb.ROOT)

    return gemini.interact_with_fallback(key, gemini.TTS_MODELS, body, stage=STAGE, params=inputs, handle=handle)


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    if "voices" not in storyboard:
        raise sb.StoryboardError("storyboard has no `voices`; add one voice per speaker")
    untranslated = [shot["id"] for shot in storyboard["shots"] for line in shot["lines"] if "spoken" not in line]
    if untranslated:
        raise sb.StoryboardError(f"lines without `spoken` text in {', '.join(untranslated)}; run pipeline.script first")

    key = os.environ["GEMINI_API_KEY"]
    made = skipped = 0
    for shot in storyboard["shots"]:
        for i, line in enumerate(shot["lines"]):
            out_path = line_audio_path(storyboard, shot, i)
            if out_path.exists():
                skipped += 1
                continue
            model, _ = synthesize(key, line_inputs(storyboard, line), out_path)
            made += 1
            print(f"{shot['id']}-{i} {line['speaker']}: {wav_duration_s(out_path):.1f} s ({model})")
    print(f"narration: {made} generated, {skipped} cached")


if __name__ == "__main__":
    load_dotenv()
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
