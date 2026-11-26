"""Projects on disk. A project is one folder with its own storyboard.json, outputs/ and runs.jsonl.

The example film is a read-only project whose folder is the repo itself.
"""

import json
import os
import re
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pipeline import keyframes, music, narration, shots
from pipeline import storyboard as sb
from pipeline.common import workspace

PROJECTS_DIR = Path(os.environ.get("VIDEOMAKER_DATA") or workspace.REPO_ROOT / "data") / "projects"
EXAMPLE_ID = "example"
ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
BLANK_STORYBOARD = Path(__file__).with_name("blank_storyboard.json")
# These stages only ever write new, hash-named files, so a remix can share them with the
# example by hard link. Other folders are rewritten in place (film-16x9.mp4, srt files), and
# writing through a hard link would change the example's copy too.
SHAREABLE_STAGES = ("narration", "keyframes", "shots", "music")
COPIED_FILES = ("film/film-16x9.mp4", "film/film-9x16.mp4")


class ProjectNotFound(LookupError):
    pass


class ReadOnlyProject(PermissionError):
    pass


def project_dir(project_id):
    if project_id == EXAMPLE_ID:
        return workspace.REPO_ROOT
    if not ID_PATTERN.match(project_id) or not (PROJECTS_DIR / project_id).is_dir():
        raise ProjectNotFound(project_id)
    return PROJECTS_DIR / project_id


def storyboard_path(project_id):
    return project_dir(project_id) / "storyboard.json"


def created_at(project_id):
    meta = project_dir(project_id) / "project.json"
    return json.loads(meta.read_text(encoding="utf-8"))["created"] if meta.exists() else None


def link_tree(source, target):
    for path in source.rglob("*"):
        if path.is_file():
            dest = target / path.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(path, dest)
            except OSError:
                shutil.copy2(path, dest)


def create(source):
    if source not in (EXAMPLE_ID, "blank"):
        raise ValueError(f"unknown source {source}; use 'example' or 'blank'")
    project_id = secrets.token_hex(16)
    folder = PROJECTS_DIR / project_id
    (folder / "outputs").mkdir(parents=True)
    if source == EXAMPLE_ID:
        example = workspace.REPO_ROOT
        shutil.copy2(example / "storyboard.json", folder / "storyboard.json")
        # The end-card credits look up which model made each reused file, so the log comes along.
        shutil.copy2(example / "runs.jsonl", folder / "runs.jsonl")
        for stage in SHAREABLE_STAGES:
            link_tree(example / "outputs" / stage, folder / "outputs" / stage)
        for name in COPIED_FILES:
            if (example / "outputs" / name).exists():
                (folder / "outputs" / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(example / "outputs" / name, folder / "outputs" / name)
    else:
        shutil.copy2(BLANK_STORYBOARD, folder / "storyboard.json")
    meta = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": source}
    (folder / "project.json").write_text(json.dumps(meta), encoding="utf-8")
    return project_id


def read_storyboard(project_id):
    return json.loads(storyboard_path(project_id).read_text(encoding="utf-8"))


def save_storyboard(project_id, storyboard):
    """Returns the validation errors; saves only when there are none."""
    if project_id == EXAMPLE_ID:
        raise ReadOnlyProject("the example film is read-only; remix it to edit")
    errors = sb.validation_errors(storyboard)
    if not errors:
        sb.save(storyboard, storyboard_path(project_id))
    return errors


def file_url(project_id, path):
    if path is None or not Path(path).exists():
        return None
    return f"/files/{project_id}/{workspace.relative(path)}"


def maybe(make_path):
    try:
        return make_path()
    except (FileNotFoundError, KeyError, sb.StoryboardError):
        return None


def outputs(project_id):
    """URLs of the current output for every part of the film, or None where it is not made yet."""
    with workspace.use(project_dir(project_id)):
        storyboard = read_storyboard(project_id)
        url = lambda make_path: file_url(project_id, maybe(make_path))
        result = {
            "references": {c: url(lambda c=c: keyframes.reference_path(storyboard, c)) for c in storyboard.get("characters", {})},
            "shots": {
                shot["id"]: {
                    "keyframe": url(lambda s=shot: keyframes.keyframe_path(storyboard, s)),
                    "clip": url(lambda s=shot: shots.best_clip(storyboard, s)),
                    "lines": [url(lambda s=shot, i=i: narration.line_audio_path(storyboard, s, i)) for i, _ in enumerate(shot["lines"])],
                }
                for shot in storyboard["shots"]
            },
            "music": [
                {"seed": seed, "url": url(lambda seed=seed: music.candidate_path(storyboard, seed))}
                for seed in storyboard.get("music", {}).get("seeds", [])
            ],
            "films": {
                orientation: file_url(project_id, workspace.outputs_dir() / "film" / f"film-{orientation}.mp4")
                for orientation in ("16x9", "9x16")
            },
        }
    return result


def output_file(project_id, relative_path):
    """The file to serve for /files/<project>/<path>, only from inside that project's outputs/."""
    outputs_root = (project_dir(project_id) / "outputs").resolve()
    path = (project_dir(project_id) / relative_path).resolve()
    if not path.is_relative_to(outputs_root) or not path.is_file():
        raise ProjectNotFound(relative_path)
    return path
