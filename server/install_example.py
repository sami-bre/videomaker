"""Copy the example film's storyboard, run log and generated files to where the server reads them.

Run: uv run python -m server.install_example [path/to/repo/checkout]

The target is VIDEOMAKER_EXAMPLE. The Docker image leaves these files out to stay small, so
on a server you run this once against a clone of the repo, with the data volume mounted.
"""

import sys
from pathlib import Path

from pipeline.common import workspace
from server import projects

if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else workspace.REPO_ROOT
    if projects.EXAMPLE_DIR.resolve() == source.resolve():
        sys.exit("VIDEOMAKER_EXAMPLE points at the source already; set it to where the files should go")
    projects.install_example(source, projects.EXAMPLE_DIR)
    print(f"example film installed in {projects.EXAMPLE_DIR}")
