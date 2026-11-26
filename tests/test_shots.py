from pipeline import shots


def test_best_clip_prefers_final_over_draft_and_wan_over_ken_burns(tmp_path, monkeypatch):
    monkeypatch.setattr(shots, "clip_path", lambda board, shot, quality, engine: tmp_path / f"{quality}.mp4")
    shot = {"id": "s01"}

    assert shots.best_clip({}, shot) is None

    (tmp_path / "draft.kenburns.mp4").touch()
    assert shots.best_clip({}, shot).name == "draft.kenburns.mp4"

    (tmp_path / "draft.mp4").touch()
    assert shots.best_clip({}, shot).name == "draft.mp4"

    (tmp_path / "final.kenburns.mp4").touch()
    assert shots.best_clip({}, shot).name == "final.kenburns.mp4"

    (tmp_path / "final.mp4").touch()
    assert shots.best_clip({}, shot).name == "final.mp4"


def test_length_check_refuses_clips_too_short_for_their_narration_or_not_makeable():
    board_shots = [{"id": "s01", "clip_s": 8}, {"id": "s02", "clip_s": 8}, {"id": "s03", "clip_s": 13}]
    lengths = {"s01": 9.5, "s02": 12.8, "s03": 12.8}

    problems = shots.length_problems(board_shots, "grok", lengths)
    assert len(problems) == 1 and problems[0].startswith("s02:") and "at least 11" in problems[0]

    assert any("cannot make a 13 s clip" in p for p in shots.length_problems(board_shots, "wan", lengths))
