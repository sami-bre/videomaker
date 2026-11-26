"""Film stage: the finished film in 16:9 and 9:16.

Run: uv run python -m pipeline.film [path/to/storyboard.json]

Each shot's clip is fitted to the narration timing (trimmed, or slowed to no less than
MIN_CLIP_SPEED), framed for the aspect ratio, and cut together with the end card. The
sound is the narration with the chosen score ducked under it, normalised in two passes
to -14 LUFS with true peaks under -1 dB. English subtitles are burned in.
"""

import json
import subprocess
import sys

from pipeline import assemble, endcard, music, shots
from pipeline import storyboard as sb
from pipeline.common.workspace import outputs_dir, relative

FPS = 24
SUBTITLE_STYLE = "FontName=Ubuntu,Bold=1,PrimaryColour=&H00222222,OutlineColour=&H00DCE8E4,BorderStyle=1,Outline=2,Shadow=0"
# (width, height, subtitle wrap width, subtitle size and margin). Vertical subtitles sit
# higher, to stay clear of the buttons and captions phone apps draw over the bottom.
ORIENTATIONS = {
    "16x9": (1280, 720, 42, "FontSize=17,MarginV=18"),
    "9x16": (720, 1280, 26, "FontSize=10,MarginV=70"),
}


def film_dir():
    return outputs_dir() / "film"


def media_duration_s(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout)


def frame_filter(shot, width, height):
    """Scale a 16:9 clip into the output frame: as is for 16:9; for 9:16, a crop at the
    shot's focus, or the whole frame over a blurred copy of itself (`fit`)."""
    if width > height:
        return f"scale={width}:{height},setsar=1"
    vertical = shot.get("vertical", {})
    if vertical.get("mode") == "fit":
        return (
            f"split=2[bg][fg];[bg]scale=-2:{height},crop={width}:{height},boxblur=25:3[bg];"
            f"[fg]scale={width}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
        )
    focus = vertical.get("focus", 0.5)
    return f"scale=-2:{height},crop={width}:{height}:(in_w-{width})*{focus}:0,setsar=1"


def normalize_loudness(in_path, out_path, target_lufs=assemble.FINAL_LUFS, true_peak=-1.5):
    """Two-pass loudnorm: measure first, then apply with the measured values, which is
    more accurate than one pass. The peak target sits below -1 dB because AAC encoding
    adds a little (a -1.0 target measured -0.8 after encoding)."""
    spec = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11"
    measure = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(in_path), "-af", f"{spec}:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    m = json.loads(measure[measure.rindex("{") : measure.rindex("}") + 1])
    second = (
        f"{spec}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
        f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(in_path), "-af", second, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(out_path)],
        check=True,
    )
    return out_path


def render(storyboard, timeline, audio, orientation):
    width, height, wrap, subtitle_size = ORIENTATIONS[orientation]
    srt = film_dir() / f"subtitles-{orientation}.srt"
    assemble.write_srt(timeline, srt, wrap)
    card = endcard.render(storyboard, film_dir() / f"endcard-{orientation}.mp4", width, height, assemble.END_CARD_S)

    inputs, chains = [], []
    for n, (plan, shot) in enumerate(zip(timeline, storyboard["shots"])):
        clip = shots.best_clip(storyboard, shot)
        shot_s = plan["end"] - plan["start"]
        _, speed = assemble.fit_clip(media_duration_s(clip), shot_s)
        inputs += ["-i", str(clip)]
        chains.append(
            f"[{n}:v:0]setpts=PTS/{speed},fps={FPS},{frame_filter(shot, width, height)},"
            f"trim=duration={shot_s:.3f},setpts=PTS-STARTPTS[v{n}];"
        )
    count = len(chains)
    inputs += ["-i", str(card), "-i", str(audio)]
    filters = (
        "".join(chains)
        + f"[{count}:v]fps={FPS},setsar=1[card];"
        + "".join(f"[v{n}]" for n in range(count))
        + f"concat=n={count}:v=1:a=0,subtitles={srt.name}:fontsdir={endcard.FONT_DIR}:force_style='{SUBTITLE_STYLE},{subtitle_size}'[story];"
        + "[story][card]concat=n=2:v=1:a=0,format=yuv420p[v]"
    )
    out = film_dir() / f"film-{orientation}.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", filters,
         "-map", "[v]", "-map", f"{count + 1}:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-r", str(FPS), "-c:a", "copy", "-movflags", "+faststart", "-shortest", out.name],
        cwd=film_dir(), check=True,
    )
    return out


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    missing = [s["id"] for s in storyboard["shots"] if shots.best_clip(storyboard, s) is None]
    track = music.chosen_track(storyboard)
    if missing or track is None or not track.exists():
        raise sb.StoryboardError(f"need a clip for every shot (missing: {missing}) and a chosen, generated score; run pipeline.shots and pipeline.music")
    film_dir().mkdir(parents=True, exist_ok=True)

    timeline = assemble.build_timeline(storyboard, assemble.line_durations(storyboard))
    total = timeline[-1]["end"] + assemble.END_CARD_S
    voice = assemble.render_narration_track(storyboard, timeline, film_dir() / "narration.wav", total)
    mix = assemble.duck_mix(voice, track, film_dir() / "mix.m4a", total)
    audio = normalize_loudness(mix, film_dir() / "soundtrack.m4a")

    for orientation in ORIENTATIONS:
        out = render(storyboard, timeline, audio, orientation)
        print(f"film {orientation}: {media_duration_s(out):.1f} s -> {relative(out)}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
