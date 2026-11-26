import copy

import pytest

from pipeline import storyboard as sb
from pipeline.common.cache import input_hash

VALID = {
    "schema_version": 1,
    "title": "Test film",
    "narration_language": "am",
    "shots": [
        {
            "id": "s01",
            "reason": "Sets the scene.",
            "description": "A boy walks.",
            "duration_s": 5,
            "lines": [{"speaker": "dad", "en": "I walked."}],
        }
    ],
}


def test_real_storyboard_is_valid():
    assert sb.load()["shots"]


def test_typo_in_field_name_is_rejected():
    board = copy.deepcopy(VALID)
    board["shots"][0]["durration_s"] = board["shots"][0].pop("duration_s")
    errors = sb.validation_errors(board)
    assert any("durration_s" in e for e in errors)
    assert any("duration_s" in e and "required" in e for e in errors)


def test_duplicate_shot_ids_are_rejected():
    board = copy.deepcopy(VALID)
    board["shots"].append(copy.deepcopy(board["shots"][0]))
    assert sb.validation_errors(board) == ["shots: id s01 is used more than once"]


def test_save_refuses_invalid_storyboard(tmp_path):
    board = copy.deepcopy(VALID)
    del board["shots"][0]["reason"]
    with pytest.raises(sb.StoryboardError):
        sb.save(board, tmp_path / "storyboard.json")
    assert not (tmp_path / "storyboard.json").exists()


def test_cache_hash_ignores_key_order_but_not_values():
    assert input_hash({"text": "hi", "voice": "Kore"}) == input_hash({"voice": "Kore", "text": "hi"})
    assert input_hash({"text": "hi", "voice": "Kore"}) != input_hash({"text": "hi!", "voice": "Kore"})
