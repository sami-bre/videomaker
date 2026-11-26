from pipeline.assemble import LINE_GAP_S, SHOT_LEAD_IN_S, SHOT_TAIL_S, build_timeline, fit_clip, subtitle_cues

BOARD = {
    "shots": [
        {"id": "s01", "duration_s": 7, "lines": [{"en": "Short line."}]},
        {"id": "s02", "duration_s": 4, "lines": [{"en": "A."}, {"en": "B."}]},
    ]
}


def test_shot_keeps_planned_length_when_speech_is_short():
    timeline = build_timeline(BOARD, {("s01", 0): 2.0, ("s02", 0): 0.5, ("s02", 1): 0.5})
    assert timeline[0]["end"] == 7
    assert timeline[1]["start"] == 7


def test_shot_stretches_to_fit_long_speech_and_pushes_later_shots():
    timeline = build_timeline(BOARD, {("s01", 0): 2.0, ("s02", 0): 3.0, ("s02", 1): 2.0})
    s02 = timeline[1]
    assert s02["lines"][1]["start"] == round(7 + SHOT_LEAD_IN_S + 3.0 + LINE_GAP_S, 3)
    assert s02["end"] == round(s02["lines"][1]["end"] + SHOT_TAIL_S, 3)


def test_long_subtitle_splits_into_two_row_cues_covering_the_line():
    text = "Then came the Blue Nile. I would hold my books over my head. There was always a hungry crocodile."
    cues = subtitle_cues(text, 10.0, 16.0)
    assert len(cues) == 2
    assert all(len(cue[2].split("\n")) <= 2 for cue in cues)
    assert cues[0][0] == 10.0 and abs(cues[-1][1] - 16.0) < 1e-9
    assert " ".join(c[2].replace("\n", " ") for c in cues) == text


def test_fit_clip_trims_long_clips_slows_slightly_short_ones_and_flags_the_rest():
    assert fit_clip(8, 7.5) == ("trim", 1.0)
    assert fit_clip(8, 10.0) == ("slow", 0.8)
    assert fit_clip(8, 12.8) == ("too_short", 0.625)
