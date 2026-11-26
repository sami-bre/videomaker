import json
import sys
import time

import pytest
from fastapi.testclient import TestClient

from pipeline import estimate
from pipeline import storyboard as sb
from pipeline.common import workspace
from pipeline.common.cache import cached_path
from pipeline.common.runlog import logged_call
from server import app as service
from server import projects
from server.runs import Runner


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(service, "runner", Runner())
    with TestClient(service.app) as test_client:
        yield test_client


def fake_pipeline(monkeypatch, code):
    monkeypatch.setattr(Runner, "command", lambda self, run: [sys.executable, "-c", code])


def wait_until_finished(client, run_id):
    for _ in range(100):
        status = client.get(f"/api/runs/{run_id}").json()["status"]
        if status in ("done", "failed", "cancelled"):
            return status
        time.sleep(0.05)
    raise AssertionError("run did not finish")


def test_a_workspace_keeps_outputs_and_the_run_log_in_its_own_folder(tmp_path):
    with workspace.use(tmp_path):
        out = cached_path("narration", "s01-0", {"text": "hi"}, ".wav")
        with logged_call("narration", "test", "test-model", {}) as record:
            record["output"] = str(workspace.relative(out))
    assert out.parent == tmp_path / "outputs" / "narration"
    assert json.loads((tmp_path / "runs.jsonl").read_text())["output"].startswith("outputs/narration/s01-0-")


def test_a_remix_with_one_edited_line_needs_one_new_voice_line_and_no_new_pictures(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path)
    project_id = projects.create(projects.EXAMPLE_ID)
    storyboard = projects.read_storyboard(project_id)
    storyboard["shots"][0]["lines"][0]["spoken"] += " እሺ"

    with workspace.use(projects.project_dir(project_id)):
        result = estimate.estimate(storyboard, ["narration", "keyframes", "shots"])

    assert result["narration"]["to_make"] == 1 and result["narration"]["needs_keys"] == ["GEMINI_API_KEY"]
    assert all(result[stage]["to_make"] == 0 and result[stage]["needs_keys"] == [] for stage in ("keyframes", "shots"))


def test_keys_reach_the_pipeline_but_never_its_log(client, monkeypatch):
    fake_pipeline(monkeypatch, "import os; print('using', os.environ['GEMINI_API_KEY'])")
    project_id = client.post("/api/projects", json={"source": "blank"}).json()["id"]
    run = client.post(
        f"/api/projects/{project_id}/runs", json={"stages": ["film"]},
        headers={"X-Provider-Keys": json.dumps({"GEMINI_API_KEY": "secret-key-123"})},
    ).json()

    assert wait_until_finished(client, run["id"]) == "done"
    log = (projects.project_dir(project_id) / "jobs" / f"{run['id']}.log").read_text()
    assert log.strip() == "using ***"


def test_saving_an_invalid_storyboard_is_refused_and_leaves_the_file_unchanged(client):
    project_id = client.post("/api/projects", json={"source": "blank"}).json()["id"]
    before = projects.storyboard_path(project_id).read_text()
    broken = {**projects.read_storyboard(project_id), "durration_s": 5}

    response = client.put(f"/api/projects/{project_id}/storyboard", json=broken)

    assert response.status_code == 422 and "durration_s" in str(response.json()["detail"]["errors"])
    assert projects.storyboard_path(project_id).read_text() == before
    assert client.put("/api/projects/example/storyboard", json=sb.load()).status_code == 403


def test_a_project_runs_one_pipeline_at_a_time(client, monkeypatch):
    fake_pipeline(monkeypatch, "import time; time.sleep(1)")
    project_id = client.post("/api/projects", json={"source": "blank"}).json()["id"]

    first = client.post(f"/api/projects/{project_id}/runs", json={"stages": ["film"]})
    second = client.post(f"/api/projects/{project_id}/runs", json={"stages": ["film"]})

    assert first.status_code == 200 and second.status_code == 409
    client.post(f"/api/runs/{first.json()['id']}/cancel")
    assert wait_until_finished(client, first.json()["id"]) == "cancelled"
