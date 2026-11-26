# videomaker

A storyboard-driven AI video pipeline. You describe a short film in one file, `storyboard.json`: its shots, narration lines, look, characters, voices and music. `make film` turns it into a finished, narrated, scored and subtitled video in 16:9 and 9:16.

```
storyboard.json ─► script ─► narration ─► keyframes ─► shots ─► music ─► film
                   (translate) (TTS per line) (reference sheet,  (image-to-  (score     (cut, duck, subtitles,
                                              then 1 per shot)   video)     candidates) end card, 16:9 + 9:16)
```

- **One contract.** Every stage reads the storyboard, which is validated against a JSON Schema on every load, and writes its own outputs. No story details live in the code.
- **Only what changed is regenerated.** Each output is named by a hash of exactly the inputs it uses. Edit one line, rerun, and one narration file is remade, not ten.
- **Every model call is logged.** `runs.jsonl` records model, params, seed, latency and cost. COSTS.md and the end-card credits are built from it.
- **It keeps going when a model fails.** It retries, falls back to the next model, makes a Ken Burns shot when video fails, and refuses to render a clip too short for its narration before any money is spent.

## Example film: *When I Was Your Age*

The repo ships with the storyboard and every generated file for an 88-second comedy, narrated in Amharic with English subtitles. Every Ethiopian kid has heard their dad's "when I was your age, I walked to school…". This is that story, taken to its comic extreme. The young dad crosses the Blue Nile past a hungry crocodile, tiptoes under an elephant in Chebera Churchura, climbs the Simien cliffs past bored geladas, and hops across the lava of Erta Ale. When he finally arrives, wet and smoking, the teacher says: **"You're late again!"**

The finished films are `outputs/film/film-16x9.mp4` and `outputs/film/film-9x16.mp4`.

## Run it

You need [uv](https://docs.astral.sh/uv/), FFmpeg with libass (`ffmpeg -filters | grep subtitles`), and Python 3.12+.

```bash
git clone https://github.com/sami-bre/videomaker.git && cd videomaker
make setup        # installs dependencies, creates .env from .env.example
# fill in the API keys in .env (see below)
make film         # storyboard.json -> outputs/film/film-16x9.mp4 and film-9x16.mp4
```

`make film` runs every stage in order: `script → narration → keyframes → shots → music → film`. This repo includes `outputs/` and `runs.jsonl`, so a fresh clone reuses every generated file and makes **no paid model calls**. Only the FFmpeg edit runs, which takes about 2 minutes. Delete `outputs/` to regenerate everything from scratch.

### API keys (`.env`)

| Key | Used for | Free? |
|---|---|---|
| `GEMINI_API_KEY` | Narration (Gemini TTS) | Free tier ([AI Studio](https://aistudio.google.com/apikey)) |
| `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | Keyframes (FLUX.2 klein 4B) | Free daily allowance |
| `OPENROUTER_API_KEY` | Video (Grok Imagine), translation fallback | Paid, cents |
| `ADDIS_API_KEY` | Amharic translation (Addis AI) | Paid in ETB, under 2 ETB per film |
| `WAVESPEED_API_KEY` | Music (ACE-Step 1.5) | $1 sign-up credit covers it |

## What it costs

For the example film, measured in `runs.jsonl` and summarised in [COSTS.md](COSTS.md) (`make costs`):
- **The calls behind the finished film: about $2.70**, mostly the 8 Grok Imagine video clips at 720p.
- **Everything we ran while building it**, including experiments, failures and retries: about $5.
- Narration, keyframes and the edit cost nothing (free tiers and FFmpeg).

## Change one shot

This is the everyday loop, and what the walkthrough shows:

1. Edit one shot in `storyboard.json`, for example its `image_prompt`, or one line's `spoken` text.
2. Run `make film`.
3. Only the outputs that depend on what you changed are regenerated. Each stage prints `N generated, M cached`, and `runs.jsonl` gets only the new calls.

Each stage names its outputs by a hash of exactly the inputs it uses. Downstream hashes include the upstream file's bytes, so a new keyframe re-animates only its own clip ([ARCHITECTURE.md](ARCHITECTURE.md#caching-only-regenerate-what-changed)).

Other commands:

```bash
make validate      # check storyboard.json against the schema
make radio         # narration-only "radio cut" for a first audience test
make shots-draft   # cheap 480p clips to check motion before paying for 720p
make costs         # rebuild COSTS.md from runs.jsonl
make smoke         # call every provider once and log it
make test          # 13 tests on the logic that would silently break a film
```

## Make your own film

Write a new `storyboard.json`. It is validated against [`schema/storyboard.schema.json`](schema/storyboard.schema.json), and `make validate` names every mistake. Set:
- the story fields: `shots[].lines[].en`, `narration_language`, `translation_notes`, `voices`;
- the look: `style`, `characters`, `image_prompt`, `motion_prompt`, `motion_style`;
- the sound and the end: `music`, `end_card`.

No story details live in the code.

## Repository

```
storyboard.json        the contract: shots, prompts, seeds, narration, voices, music, framing
schema/                JSON Schema for the storyboard, validated on every load
pipeline/              one module per stage, plus run.py (everything) and costs.py
  common/              logging, retries, caching, provider clients
tests/                 13 tests
runs.jsonl             one line per model call: model, params, seed, latency, cost, output
outputs/               every generated image, audio file and video, kept for inspection
assets/fonts/          end-card font and its licence
docs/research/         provider research: prices, free tiers, licences, sources
```

| Document | What's in it |
|---|---|
| [DESIGN.md](DESIGN.md) | Audience, intent, every decision and why, shot reasons, both user tests |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Stages, the storyboard contract, caching, failure handling |
| [EXPERIMENTS.md](EXPERIMENTS.md) | Hypothesis → change → result: translators, styles, video engines, the score |
| [FAILURES.md](FAILURES.md) | What broke, what we tried, what fixed it |
| [COSTS.md](COSTS.md) | Measured latency and spend per stage and model, generated from the log |
| [ETHICS.md](ETHICS.md) | Consent, licences, labelling |
