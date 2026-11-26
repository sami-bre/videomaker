"""Pipeline runs: one subprocess each, at most MAX_PARALLEL_RUNS at once, one per project.

The user's keys go only into that subprocess's environment. Every line it prints has the
key values replaced with *** before it is stored or sent to the browser.
"""

import asyncio
import json
import os
import secrets
import sys
from dataclasses import dataclass, field

from pipeline import run as pipeline_run
from pipeline.common import workspace
from server import projects

MAX_PARALLEL_RUNS = 2
KEY_NAMES = (
    "OPENROUTER_API_KEY", "ADDIS_API_KEY", "GEMINI_API_KEY",
    "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "WAVESPEED_API_KEY",
)
MIN_SECRET_LENGTH = 6


class ProjectBusy(RuntimeError):
    pass


def scrub(text, keys):
    for value in keys.values():
        if len(value) >= MIN_SECRET_LENGTH:
            text = text.replace(value, "***")
    return text


@dataclass
class Run:
    id: str
    project_id: str
    stages: list
    quality: str
    status: str = "queued"
    stage_status: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    listeners: list = field(default_factory=list)
    process: asyncio.subprocess.Process | None = None
    cancelled: bool = False

    def publish(self, event):
        self.events.append(event)
        for queue in self.listeners:
            queue.put_nowait(event)

    def summary(self):
        return {"id": self.id, "project_id": self.project_id, "stages": self.stages, "quality": self.quality,
                "status": self.status, "stage_status": self.stage_status}


class Runner:
    def __init__(self, max_parallel=MAX_PARALLEL_RUNS):
        self.runs = {}
        self.active_by_project = {}
        self.slots = asyncio.Semaphore(max_parallel)

    def active_run(self, project_id):
        run_id = self.active_by_project.get(project_id)
        return self.runs.get(run_id) if run_id else None

    def queue_position(self, run):
        queued = [r.id for r in self.runs.values() if r.status == "queued" and not r.cancelled]
        return queued.index(run.id) + 1 if run.id in queued else 0

    def start(self, project_id, stages, quality, keys):
        if self.active_run(project_id):
            raise ProjectBusy("this project already has a run going")
        run = Run(secrets.token_hex(8), project_id, stages, quality)
        self.runs[run.id] = run
        self.active_by_project[project_id] = run.id
        asyncio.get_running_loop().create_task(self.execute(run, {k: v for k, v in keys.items() if k in KEY_NAMES and v}))
        return run

    def command(self, run):
        return [
            sys.executable, "-m", "pipeline.run", str(projects.storyboard_path(run.project_id)),
            "--stages", ",".join(run.stages), "--quality", run.quality, "--events",
        ]

    def environment(self, run, keys):
        return {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "PYTHONUNBUFFERED": "1",
            "VIDEOMAKER_SERVICE": "1",
            "VIDEOMAKER_WORKSPACE": str(projects.project_dir(run.project_id)),
            **keys,
        }

    async def execute(self, run, keys):
        log_dir = projects.project_dir(run.project_id) / "jobs"
        log_dir.mkdir(exist_ok=True)
        try:
            async with self.slots:
                if run.cancelled:
                    return
                run.status = "running"
                run.publish({"type": "status", "status": "running"})
                run.process = await asyncio.create_subprocess_exec(
                    *self.command(run), cwd=workspace.REPO_ROOT, env=self.environment(run, keys),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                )
                with (log_dir / f"{run.id}.log").open("w", encoding="utf-8") as log:
                    async for raw in run.process.stdout:
                        line = scrub(raw.decode("utf-8", "replace").rstrip("\n"), keys)
                        log.write(line + "\n")
                        log.flush()
                        self.handle_line(run, line)
                code = await run.process.wait()
                run.status = "cancelled" if run.cancelled else ("done" if code == 0 else "failed")
        except Exception as exc:
            run.status = "failed"
            run.publish({"type": "log", "line": scrub(f"server error: {exc}", keys)})
        finally:
            self.active_by_project.pop(run.project_id, None)
            run.publish({"type": "status", "status": run.status})

    def handle_line(self, run, line):
        if line.startswith(pipeline_run.EVENT_PREFIX):
            event = json.loads(line[len(pipeline_run.EVENT_PREFIX):])
            run.stage_status[event["stage"]] = event["status"]
            run.publish({"type": "stage", **event})
        else:
            run.publish({"type": "log", "line": line})

    def cancel(self, run):
        run.cancelled = True
        if run.process and run.process.returncode is None:
            run.process.terminate()
