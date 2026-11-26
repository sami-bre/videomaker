"""Where a run reads and writes: the repo itself for the CLI, or one project folder for the web service.

A subprocess picks its folder from VIDEOMAKER_WORKSPACE. The web server, which serves many
projects from one process, switches folders per request with `use()`.
"""

import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_MODE = os.environ.get("VIDEOMAKER_SERVICE") == "1"
_current = ContextVar("workspace", default=Path(os.environ.get("VIDEOMAKER_WORKSPACE") or REPO_ROOT).resolve())


def root():
    return _current.get()


def outputs_dir():
    return root() / "outputs"


def runs_file():
    return root() / "runs.jsonl"


@contextmanager
def use(path):
    token = _current.set(Path(path).resolve())
    try:
        yield
    finally:
        _current.reset(token)


def relative(path):
    return Path(path).resolve().relative_to(root())


def load_keys():
    # In the web service each run carries the user's own keys; reading the server's .env would spend the server's money.
    if not SERVICE_MODE:
        load_dotenv(REPO_ROOT / ".env")


class MissingKey(RuntimeError):
    pass


def require_key(name):
    """Read an API key only when a model call is about to use it, so a fully cached run needs no keys."""
    value = os.environ.get(name)
    if not value:
        raise MissingKey(f"missing API key {name}")
    return value
