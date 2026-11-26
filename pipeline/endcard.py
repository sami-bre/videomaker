"""The closing "Made with AI" card, in the film's doodle look, with small credits that say
which model made which part. The credits are read from runs.jsonl for the exact files in
the film, so they can only name models that were really used.
"""

import subprocess

from pipeline import keyframes, music, narration, script, shots
from pipeline import storyboard as sb
from pipeline.common import addis
from pipeline.common.runlog import models_by_output_name

FONT_DIR = sb.ROOT / "assets" / "fonts"
TITLE_FONT, BODY_FONT = FONT_DIR / "Ubuntu-B.ttf", FONT_DIR / "Ubuntu-L.ttf"
PAPER, INK = "0xE4E8DC", "0x222222"

MODEL_NAMES = {
    # The card font has no Ge'ez letters, so the model name stays out of the display name.
    "Addis-፩-አሌፍ": "Addis AI",
    "google/gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-3.8-flash-tts": "Gemini 3.8 Flash TTS",
    "gemini-3.8-flash-lite-tts": "Gemini 3.8 Flash-Lite TTS",
    "gemini-2.5-flash-preview-tts": "Gemini 2.5 Flash TTS",
    "@cf/black-forest-labs/flux-2-klein-4b": "FLUX.2 klein 4B on Cloudflare Workers AI",
    "x-ai/grok-imagine-video-1.5-lite": "Grok Imagine Video 1.5 Lite via OpenRouter",
    "wavespeed-ai/wan-2.2/i2v-480p-ultra-fast": "Wan 2.2 via WaveSpeed",
    "wavespeed-ai/wan-2.2/i2v-720p-ultra-fast": "Wan 2.2 via WaveSpeed",
    "wavespeed-ai/ace-step-1.5": "ACE-Step 1.5 via WaveSpeed",
}


def credit_lines(storyboard):
    made_by = models_by_output_name()

    def models_for(paths):
        names = sorted({MODEL_NAMES.get(made_by.get(p.name), made_by.get(p.name)) for p in paths if p and p.name in made_by})
        return ", ".join(names) or "unknown"

    used_characters = sorted({c for shot in storyboard["shots"] for c in shot.get("characters", [])})
    pictures = [keyframes.keyframe_path(storyboard, s) for s in storyboard["shots"]] + [
        keyframes.reference_path(storyboard, c) for c in used_characters
    ]
    translator = addis.CHAT_MODEL if storyboard["narration_language"] in script.ADDIS_LANGUAGES else script.FALLBACK_MODEL
    lines = [
        ("Translation", MODEL_NAMES.get(translator, translator) + ", fixed by a native speaker"),
        ("Voices", models_for([narration.line_audio_path(storyboard, s, i) for s in storyboard["shots"] for i, _ in enumerate(s["lines"])])),
        ("Pictures", models_for(pictures)),
        ("Motion", models_for([shots.best_clip(storyboard, s) for s in storyboard["shots"]])),
        ("Music", models_for([music.chosen_track(storyboard)])),
        ("Edit", "FFmpeg, no AI"),
        ("Pipeline code", "written with Claude Code"),
    ]
    made_by_human = storyboard.get("end_card", {}).get("made_by")
    head = [f"Story, script and direction: {made_by_human}"] if made_by_human else ["Story, script and direction by a human"]
    return head + [f"{role}: {who}" for role, who in lines]


def escape_text(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def render(storyboard, out_path, width, height, seconds):
    """A still card with the kuncho boy, the title and the credits, fading in from black."""
    vertical = height > width
    boy = keyframes.reference_path(storyboard, "young_dad")
    title = escape_text(storyboard.get("end_card", {}).get("title", "Made with AI"))
    credits = credit_lines(storyboard)
    credits_file = out_path.with_suffix(".credits.txt")
    credits_file.write_text("\n".join(credits), encoding="utf-8")

    if vertical:
        boy_size, boy_x, boy_y = 420, (width - 420) // 2, 150
        title_x, title_y, text_x, text_y, body_size = "(w-text_w)/2", 640, 60, 760, 20
    else:
        boy_size, boy_x, boy_y = 420, 70, (height - 420) // 2
        title_x, title_y, text_x, text_y, body_size = "540", 190, 540, 300, 20

    filters = (
        f"color=c={PAPER}:s={width}x{height}:d={seconds}:r=24[bg];"
        f"[0:v]scale={boy_size}:{boy_size},drawbox=c={INK}:t=3,format=rgba[boy];"
        f"[bg][boy]overlay={boy_x}:{boy_y},"
        f"drawtext=fontfile={TITLE_FONT}:text='{title}':fontsize=64:fontcolor={INK}:x={title_x}:y={title_y},"
        f"drawtext=fontfile={BODY_FONT}:textfile={credits_file}:fontsize={body_size}:line_spacing=12:fontcolor={INK}:x={text_x}:y={text_y},"
        f"fade=t=in:st=0:d=0.5,format=yuv420p[v]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(boy), "-filter_complex", filters,
         "-map", "[v]", "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)],
        check=True,
    )
    return out_path
