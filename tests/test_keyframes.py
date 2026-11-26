from pipeline import keyframes as kf

BOARD = {
    "style": "Flat cartoon.",
    "characters": {"boy": {"description": "a boy in a blue shirt", "seed": 1}},
    "shots": [
        {"id": "s01", "image_prompt": "A boy on a path.", "characters": ["boy"], "seed": 5},
        {"id": "s02", "image_prompt": "An empty hill.", "characters": [], "seed": 6},
    ],
}


def test_new_reference_image_changes_only_keyframes_that_show_that_character(tmp_path, monkeypatch):
    ref = tmp_path / "boy.small.png"
    monkeypatch.setattr(kf, "reference_input_path", lambda board, c: ref)
    ref.write_bytes(b"first reference")
    before = [kf.keyframe_inputs(BOARD, s) for s in BOARD["shots"]]
    ref.write_bytes(b"second reference")
    after = [kf.keyframe_inputs(BOARD, s) for s in BOARD["shots"]]
    assert before[0] != after[0]
    assert before[1] == after[1]


def test_keyframe_prompt_leads_with_action_and_carries_style_and_each_character():
    prompt = kf.keyframe_prompt(BOARD, BOARD["shots"][0])
    assert prompt.startswith("A boy on a path.")
    assert "reference image 0: a boy in a blue shirt" in prompt
    assert prompt.endswith("Flat cartoon.")
