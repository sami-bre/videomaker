# One image: the pipeline, the API and the built frontend. Project data lives on a volume at /data.
# The example film's files are not in the image; install them onto the volume once (see README).
FROM node:24-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# uv is only needed to install the Python packages, so it stays in this stage.
FROM python:3.14-slim AS python
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=python /app/.venv ./.venv
COPY . .
COPY --from=web /web/dist ./web/dist
ENV VIDEOMAKER_DATA=/data VIDEOMAKER_EXAMPLE=/data/example PATH="/app/.venv/bin:$PATH"
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
