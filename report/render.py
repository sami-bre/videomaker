"""Render report/REPORT.md to report/report.pdf with a fixed stylesheet.

Run: uv run python report/render.py   (or: make report)

Markdown -> HTML (python-markdown) -> PDF (headless Chrome). The look comes only from
style.css and the bundled Ubuntu fonts, so editing the text and re-rendering keeps the
same layout. Amharic uses the system's Noto Sans Ethiopic.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SOURCE, HTML, PDF = HERE / "REPORT.md", HERE / "report.html", HERE / "report.pdf"
CHROME_NAMES = ("google-chrome", "chromium", "chromium-browser", "chrome")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<link rel="stylesheet" href="style.css"></head>
<body>{body}</body></html>
"""


def find_chrome():
    for name in CHROME_NAMES:
        if path := shutil.which(name):
            return path
    sys.exit(f"no Chrome found; install one of: {', '.join(CHROME_NAMES)}")


LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")


def separate_lists(text):
    """Add the blank line python-markdown needs before a list, so a list right after a
    sentence ("Two things:" then "- one") renders as a list, as it does on GitHub."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        previous = lines[i - 1] if i else ""
        if LIST_ITEM.match(line) and previous.strip() and not LIST_ITEM.match(previous) and not previous.startswith((" ", "\t")):
            out.append("")
        out.append(line)
    return "\n".join(out)


def build_html():
    text = separate_lists(SOURCE.read_text(encoding="utf-8"))
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    title = text.splitlines()[0].lstrip("# ").strip()
    HTML.write_text(PAGE.format(title=title, body=body), encoding="utf-8")


def print_pdf():
    subprocess.run(
        [
            find_chrome(), "--headless", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
            "--no-pdf-header-footer", f"--print-to-pdf={PDF}", HTML.as_uri(),
        ],
        check=True, capture_output=True,
    )


if __name__ == "__main__":
    build_html()
    print_pdf()
    print(f"{PDF.relative_to(HERE.parent)} written")
