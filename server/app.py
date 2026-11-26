"""The videomaker web service: the example film, projects, storyboard editing, runs and outputs.

Run: uv run uvicorn server.app:app --reload   (or: make serve)
"""

import asyncio
import json

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline import assemble, costs, estimate, shots
from pipeline import run as pipeline_run
from pipeline import storyboard as sb
from pipeline.common import workspace
from server import projects
from server.runs import KEY_NAMES, ProjectBusy, Runner

WEB_DIST = workspace.REPO_ROOT / "web" / "dist"

app = FastAPI(title="videomaker")
runner = Runner()


class NewProject(BaseModel):
    source: str = projects.EXAMPLE_ID


class RunRequest(BaseModel):
    stages: list[str]
    quality: str = "final"


def known_project(project_id):
    try:
        return projects.project_dir(project_id)
    except projects.ProjectNotFound:
        raise HTTPException(404, "no such project")


def checked_stages(stages, quality):
    if not stages or any(s not in pipeline_run.STAGES for s in stages):
        raise HTTPException(400, f"stages must be some of {list(pipeline_run.STAGES)}")
    if quality not in ("draft", "final"):
        raise HTTPException(400, "quality must be draft or final")
    return [s for s in pipeline_run.STAGES if s in stages]


def project_estimate(project_id, stages, quality):
    with workspace.use(known_project(project_id)):
        try:
            storyboard = sb.load(projects.storyboard_path(project_id))
        except sb.StoryboardError as exc:
            raise HTTPException(422, str(exc))
        return storyboard, estimate.estimate(storyboard, stages, quality)


def clip_length_problems(project_id, storyboard, stages):
    if "shots" not in stages:
        return []
    with workspace.use(known_project(project_id)):
        try:
            lengths = assemble.shot_lengths(storyboard)
        except (sb.StoryboardError, FileNotFoundError, KeyError):
            return []
        return shots.length_problems(storyboard["shots"], storyboard.get("video_engine", "wan"), lengths)


@app.get("/api/schema")
def schema():
    return json.loads(sb.SCHEMA_PATH.read_text(encoding="utf-8"))


@app.get("/api/showcase")
def showcase():
    return {"storyboard": projects.read_storyboard(projects.EXAMPLE_ID), "outputs": projects.outputs(projects.EXAMPLE_ID)}


@app.post("/api/projects")
def create_project(body: NewProject):
    try:
        return {"id": projects.create(body.source)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/projects/{project_id}/storyboard")
def get_storyboard(project_id: str):
    known_project(project_id)
    return projects.read_storyboard(project_id)


@app.put("/api/projects/{project_id}/storyboard")
def put_storyboard(project_id: str, storyboard: dict):
    known_project(project_id)
    if runner.active_run(project_id):
        raise HTTPException(409, "a run is going; wait for it to finish before saving")
    try:
        errors = projects.save_storyboard(project_id, storyboard)
    except projects.ReadOnlyProject as exc:
        raise HTTPException(403, str(exc))
    if errors:
        raise HTTPException(422, {"errors": errors})
    return {"ok": True}


@app.get("/api/projects/{project_id}/outputs")
def get_outputs(project_id: str):
    known_project(project_id)
    return projects.outputs(project_id)


@app.post("/api/projects/{project_id}/estimate")
def post_estimate(project_id: str, body: RunRequest):
    stages = checked_stages(body.stages, body.quality)
    storyboard, result = project_estimate(project_id, stages, body.quality)
    return {"stages": result, "problems": clip_length_problems(project_id, storyboard, stages)}


@app.post("/api/projects/{project_id}/runs")
async def start_run(project_id: str, body: RunRequest, x_provider_keys: str = Header(default="{}")):
    if project_id == projects.EXAMPLE_ID:
        raise HTTPException(403, "the example film is read-only; remix it to run")
    stages = checked_stages(body.stages, body.quality)
    try:
        keys = {k: str(v).strip() for k, v in json.loads(x_provider_keys).items() if k in KEY_NAMES and v}
    except (json.JSONDecodeError, AttributeError):
        raise HTTPException(400, "X-Provider-Keys must be a JSON object")
    storyboard, result = await asyncio.to_thread(project_estimate, project_id, stages, body.quality)
    missing = sorted({k for stage in result.values() for k in stage["needs_keys"]} - set(keys))
    if missing:
        raise HTTPException(400, {"missing_keys": missing})
    problems = await asyncio.to_thread(clip_length_problems, project_id, storyboard, stages)
    if problems:
        raise HTTPException(400, {"problems": problems})
    try:
        run = runner.start(project_id, stages, body.quality, keys)
    except ProjectBusy as exc:
        raise HTTPException(409, str(exc))
    return run.summary()


@app.get("/api/projects/{project_id}/runs/active")
def active_run(project_id: str):
    known_project(project_id)
    run = runner.active_run(project_id)
    return run.summary() if run else None


def known_run(run_id):
    run = runner.runs.get(run_id)
    if not run:
        raise HTTPException(404, "no such run")
    return run


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = known_run(run_id)
    return {**run.summary(), "queue_position": runner.queue_position(run)}


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: str, request: Request):
    run = known_run(run_id)

    async def stream():
        queue = asyncio.Queue()
        backlog = list(run.events)
        run.listeners.append(queue)
        try:
            for event in backlog:
                yield f"data: {json.dumps(event)}\n\n"
            if run.status in ("done", "failed", "cancelled"):
                return
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] == "status" and event["status"] in ("done", "failed", "cancelled"):
                    return
        finally:
            run.listeners.remove(queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    runner.cancel(known_run(run_id))
    return {"ok": True}


@app.get("/api/projects/{project_id}/costs")
def project_costs(project_id: str):
    folder = known_project(project_id)
    with workspace.use(folder):
        records = costs.load_runs() if workspace.runs_file().exists() else []
    since = projects.created_at(project_id)
    own = [r for r in records if not since or r["ts"] >= since]
    by_stage = {}
    for record in own:
        by_stage.setdefault(record["stage"], []).append(record)
    return {"total": costs.summarize(own), "by_stage": {stage: costs.summarize(rs) for stage, rs in by_stage.items()}}


@app.get("/files/{project_id}/{path:path}")
def get_file(project_id: str, path: str):
    known_project(project_id)
    try:
        return FileResponse(projects.output_file(project_id, path))
    except projects.ProjectNotFound:
        raise HTTPException(404, "no such file")


if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
