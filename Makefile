STORYBOARD ?= storyboard.json

.PHONY: film setup validate radio shots-draft costs smoke test serve web web-dev report

# The whole pipeline: storyboard -> script -> narration -> keyframes -> shots -> music -> film.
film:
	uv run python -m pipeline.run $(STORYBOARD)

setup:
	uv sync
	@test -f .env || (cp .env.example .env && echo "Created .env: fill in your API keys")

validate:
	uv run python -m pipeline.storyboard $(STORYBOARD)

# Narration over a placeholder pad on a black screen, for the first user test.
radio:
	uv run python -m pipeline.script $(STORYBOARD)
	uv run python -m pipeline.narration $(STORYBOARD)
	uv run python -m pipeline.assemble $(STORYBOARD)

# Cheap 480p clips for checking motion before paying for finals.
shots-draft:
	uv run python -m pipeline.shots $(STORYBOARD)

costs:
	uv run python -m pipeline.costs

smoke:
	uv run python -m pipeline.smoke_test $(ONLY)

test:
	uv run pytest -q

# The web service: API + the built frontend on http://localhost:8000 (run `make web` first).
serve:
	uv run uvicorn server.app:app --port 8000

web:
	cd web && npm ci && npm run build

# Frontend with hot reload on http://localhost:5173; it talks to `make serve`.
web-dev:
	cd web && npm run dev

# report/REPORT.md -> report/report.pdf (needs Chrome or Chromium).
report:
	uv run python report/render.py
