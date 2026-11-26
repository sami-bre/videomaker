"""Assemble stage: the timeline, subtitles and sound shared by every cut, and the radio
cut (narration over a placeholder pad on a black screen, with English subtitles). Shot
lengths come from the narration, never shorter than the storyboard's `duration_s`. The
finished film is built from these pieces by pipeline/film.py.

Run: uv run python -m pipeline.assemble [path/to/storyboard.json]
"""

import json
import subprocess
import sys

from pipeline import narration
from pipeline import storyboard as sb
from pipeline.common.cache import OUTPUTS_DIR

SHOT_LEAD_IN_S = 0.3
LINE_GAP_S = 0.35
SHOT_TAIL_S = 0.6
SUBTITLE_LINE_CHARS = 42
WIDTH, HEIGHT, FPS = 1280, 720, 24
# A clip shorter than its shot is slowed down to fill it, but never below this speed:
# slower than 0.8x the motion looks sluggish. Shots that would need more are refused
# by the shots stage before any money is spent.
MIN_CLIP_SPEED = 0.8
END_CARD_S = 3.0


def build_timeline(storyboard, line_durations):
    """Place every shot and line on one clock.

    `line_durations` maps (shot_id, line_index) to seconds of speech. A shot lasts
    `duration_s`, or longer if its lines need more room.
    """
    timeline, t = [], 0.0
    for shot in storyboard["shots"]:
        cursor, lines = t + SHOT_LEAD_IN_S, []
        for i, line in enumerate(shot["lines"]):
            length = line_durations[(shot["id"], i)]
            lines.append({"index": i, "start": round(cursor, 3), "end": round(cursor + length, 3), "en": line["en"]})
            cursor += length + LINE_GAP_S
        speech_end = lines[-1]["end"] + SHOT_TAIL_S if lines else t
        end = round(max(t + shot["duration_s"], speech_end), 3)
        timeline.append({"id": shot["id"], "start": round(t, 3), "end": end, "lines": lines})
        t = end
    return timeline


def fit_clip(clip_s, shot_s):
    """How to make a clip fill its shot: ("trim", 1.0) if it is long enough, ("slow", speed)
    if slowing it to at least MIN_CLIP_SPEED is enough, ("too_short", speed) otherwise."""
    if clip_s >= shot_s:
        return "trim", 1.0
    speed = round(clip_s / shot_s, 3)
    return ("slow" if speed >= MIN_CLIP_SPEED else "too_short"), speed


def line_durations(storyboard):
    """Seconds of speech per (shot_id, line_index), from the narration stage's files."""
    durations = {}
    for shot in storyboard["shots"]:
        for i, _ in enumerate(shot["lines"]):
            audio = narration.line_audio_path(storyboard, shot, i)
            if not audio.exists():
                raise sb.StoryboardError(f"missing narration for {shot['id']}-{i}; run pipeline.narration first")
            durations[(shot["id"], i)] = narration.wav_duration_s(audio)
    return durations


def shot_lengths(storyboard):
    """Final length of each shot in seconds, as the edit will cut it."""
    return {shot["id"]: shot["end"] - shot["start"] for shot in build_timeline(storyboard, line_durations(storyboard))}


def wrap_words(text, width=SUBTITLE_LINE_CHARS):
    rows, row = [], ""
    for word in text.split():
        if row and len(row) + 1 + len(word) > width:
            rows.append(row)
            row = word
        else:
            row = f"{row} {word}".strip()
    return rows + [row] if row else rows


def subtitle_cues(text, start, end, width=SUBTITLE_LINE_CHARS):
    """Split one line into cues of at most two rows, timed in proportion to their length."""
    rows = wrap_words(text, width)
    chunks = ["\n".join(rows[i : i + 2]) for i in range(0, len(rows), 2)]
    total_chars = sum(len(c) for c in chunks)
    cues, t = [], start
    for chunk in chunks:
        chunk_end = t + (end - start) * len(chunk) / total_chars
        cues.append((t, chunk_end, chunk))
        t = chunk_end
    return cues


def srt_time(seconds):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def write_srt(timeline, path, width=SUBTITLE_LINE_CHARS):
    cues = [cue for shot in timeline for line in shot["lines"] for cue in subtitle_cues(line["en"], line["start"], line["end"], width)]
    path.write_text(
        "\n".join(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n" for n, (a, b, text) in enumerate(cues, 1)),
        encoding="utf-8",
    )


# Sidechain ducking settings from the challenge's tips, tuned by ear later if needed.
DUCK = "threshold=0.02:ratio=6:attack=300:release=1500"
VOICE_LUFS, MUSIC_LUFS, FINAL_LUFS = -16, -26, -14


def render_narration_track(storyboard, timeline, out_path, total_s):
    """Every narration line placed at its timeline start, as one 48 kHz stereo WAV."""
    clips = [
        (narration.line_audio_path(storyboard, shot, line["index"]), line["start"])
        for shot_plan, shot in zip(timeline, storyboard["shots"])
        for line in shot_plan["lines"]
    ]
    inputs = [arg for path, _ in clips for arg in ("-i", str(path))]
    delays = "".join(f"[{n}:a]adelay={round(start * 1000)}:all=1[a{n}];" for n, (_, start) in enumerate(clips))
    mix = "".join(f"[a{n}]" for n in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{total_s},loudnorm=I={VOICE_LUFS}:TP=-2[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", delays + mix, "-map", "[out]", str(out_path)], check=True)
    return out_path


def duck_mix(voice_path, music_path, out_path, total_s):
    """Music brought to a quiet level, ducked under the voice, then the mix set to -14 LUFS."""
    filters = (
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total_s},afade=t=out:st={total_s - 2}:d=2,loudnorm=I={MUSIC_LUFS}[m];"
        f"[0:a]asplit[v1][v2];[m][v1]sidechaincompress={DUCK}[ducked];"
        f"[ducked][v2]amix=inputs=2:normalize=0,loudnorm=I={FINAL_LUFS}:TP=-1[out]"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(voice_path), "-i", str(music_path), "-filter_complex", filters, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_path)], check=True)
    return out_path


def render_radio_cut(storyboard, timeline, out_dir):
    total = timeline[-1]["end"]
    clips = [
        (narration.line_audio_path(storyboard, shot, line["index"]), line["start"])
        for shot_plan, shot in zip(timeline, storyboard["shots"])
        for line in shot_plan["lines"]
    ]
    inputs = [arg for path, _ in clips for arg in ("-i", str(path))]
    delays = "".join(f"[{n}:a]adelay={round(start * 1000)}:all=1[a{n}];" for n, (_, start) in enumerate(clips))
    # A quiet A-minor drone: placeholder until the music stage exists.
    pad = f"aevalsrc='0.015*sin(2*PI*110*t)+0.010*sin(2*PI*164.81*t)+0.008*sin(2*PI*220*t)':s=48000:d={total}"
    filters = (
        delays
        + "".join(f"[a{n}]" for n in range(len(clips)))
        + f"amix=inputs={len(clips)}:normalize=0,aresample=48000,apad,atrim=0:{total}[voice];"
        + f"{pad}[pad];[voice][pad]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1[aout];"
        + f"color=black:s={WIDTH}x{HEIGHT}:r={FPS}:d={total},"
        + "subtitles=radio_cut.srt:force_style='FontSize=22,MarginV=40'[vout]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", filters,
         "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ac", "2", "radio_cut.mp4"],
        cwd=out_dir, check=True,
    )
    return out_dir / "radio_cut.mp4"


def run(path=sb.DEFAULT_PATH):
    storyboard = sb.load(path)
    timeline = build_timeline(storyboard, line_durations(storyboard))
    out_dir = OUTPUTS_DIR / "assemble"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    write_srt(timeline, out_dir / "radio_cut.srt")
    video = render_radio_cut(storyboard, timeline, out_dir)

    for shot in timeline:
        planned = next(s["duration_s"] for s in storyboard["shots"] if s["id"] == shot["id"])
        length = shot["end"] - shot["start"]
        print(f"{shot['id']}: {length:5.1f} s" + (f"  (stretched from {planned:g} s)" if length > planned + 0.01 else ""))
    print(f"radio cut: {timeline[-1]['end']:.1f} s -> {video.relative_to(sb.ROOT)}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else sb.DEFAULT_PATH)
