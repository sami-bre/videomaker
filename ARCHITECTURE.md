# Architecture

One file, `storyboard.json`, is the contract between every stage. Each stage is a script that reads the storyboard, writes its own outputs under `outputs/<stage>/`, and logs every model call to `runs.jsonl`. No stage calls another stage's model. The only way information moves between stages is the storyboard and the files on disk.

```
                          storyboard.json  (validated against schema/storyboard.schema.json)
                                 │
   ┌──────────┬──────────────┬───┴────────┬──────────────┬──────────────┐
   ▼          ▼              ▼            ▼              ▼              ▼
 script   narration      keyframes      shots          music          film
 (en→am)  (TTS per line) (refs, then    (image→video   (score         (cut, duck, subtitles,
   │          │           1 per shot)    per shot)      candidates)    end card, 16:9 + 9:16)
   │          ▼              ▼            ▼              ▼              ▼
   │   outputs/narration outputs/keyframes outputs/shots outputs/music  outputs/film
   └─► writes `spoken` back into storyboard.json (the only stage that edits it)

 every model call ──► runs.jsonl ──► COSTS.md (make costs) and the end-card credits
```

Run it all with `make film` (`pipeline/run.py`), or any stage alone with `uv run python -m pipeline.<stage>`.

## The contract: `storyboard.json`

The schema (`schema/storyboard.schema.json`) grew one stage at a time. Each stage added only the fields it reads. Unknown fields are rejected (`additionalProperties: false`), so a typo like `durration_s` fails at once instead of being silently ignored. `pipeline/storyboard.py` adds checks that JSON Schema cannot express: unique shot ids, a voice for every speaker, and known characters in every shot. Every stage calls `storyboard.load()`, which validates, so no stage ever runs on a broken storyboard. `storyboard.save()` refuses to write an invalid one.

| Field | Read by | Purpose |
|---|---|---|
| `shots[].id`, `reason`, `description`, `duration_s` | all | Stable id used in file names; why the shot exists; the planned minimum length |
| `shots[].lines[]` (`speaker`, `en`, `spoken`, `spoken_from_en`) | script, narration, film | English for subtitles and translation; spoken text in `narration_language` |
| `narration_language`, `translation_notes` | script | Target language; story-specific instructions (past habitual, spellings) |
| `voices` | narration | One TTS voice and delivery style per speaker |
| `style`, `characters`, `shots[].characters`, `image_prompt`, `seed` | keyframes | Fixed look and character descriptions; per-shot picture |
| `motion_style`, `video_engine`, `shots[].motion_prompt`, `clip_s` | shots | Motion and camera only; which engine's clips the film uses; clip length |
| `music` (`caption`, `seeds`, `chosen_seed`, `why_chosen`) | music, film | One cue for the film; the chosen candidate and why |
| `shots[].vertical`, `end_card` | film | 9:16 framing per shot (`crop` at a focus, or `fit`); end-card text |

Story details never live in code. A new film needs a new storyboard, not new code.

## Stages

| Stage | Module | Model (provider) | Output |
|---|---|---|---|
| script | `pipeline/script.py` | Addis AI chat `Addis-፩-አሌፍ`, fallback Gemini 2.5 Flash (OpenRouter) | `spoken` text in the storyboard |
| narration | `pipeline/narration.py` | Gemini 3.8 Flash TTS → Flash-Lite TTS → 2.5 Flash TTS | `outputs/narration/<shot>-<line>-<hash>.wav` |
| keyframes | `pipeline/keyframes.py` | FLUX.2 klein 4B (Cloudflare Workers AI) | `ref-<character>-<hash>.png`, `<shot>-<hash>.png` |
| shots | `pipeline/shots.py` | Grok Imagine Video 1.5 Lite (OpenRouter) or Wan 2.2 (WaveSpeed) | `<shot>-<engine>-<quality>-<hash>.mp4` |
| music | `pipeline/music.py` | ACE-Step 1.5 (WaveSpeed) | `seed<n>-<hash>.mp3` |
| radio cut | `pipeline/assemble.py` | none (FFmpeg) | `outputs/assemble/radio_cut.mp4` |
| film | `pipeline/film.py`, `pipeline/endcard.py` | none (FFmpeg) | `outputs/film/film-16x9.mp4`, `film-9x16.mp4` |

Shared code lives in `pipeline/common/`:
- `runlog.py` logs every call.
- `http.py` handles retries.
- `cache.py` hashes inputs.
- `gemini.py`, `openrouter.py`, `addis.py`, `cloudflare.py` and `wavespeed.py` are the provider clients.

## Caching: only regenerate what changed

`pipeline/common/cache.py` names every output `<name>-<hash>.<ext>`. The hash is a SHA-256 of **exactly the inputs that stage uses**, with keys sorted. If the file exists, the stage skips the model call. Old files are kept, so earlier takes can be compared.

| Stage | Hash inputs |
|---|---|
| narration | spoken text, voice, style, language |
| keyframes (reference) | style + description prompt, size, seed, model |
| keyframes (shot) | full prompt, size, seed, model, **bytes of the reference images used** |
| shots | **bytes of the keyframe**, motion prompt (incl. `motion_style`), clip length, seed, model, resolution |
| music | caption, film length, seed, model |
| script | not hashed: a line is retranslated when `en` differs from `spoken_from_en`; a hand edit of `spoken` is kept |

Because a downstream hash includes the upstream file's bytes, changes ripple only where they should. A new dad reference regenerated the dad's reference and s01 only (2 of 12 images, EXPERIMENTS.md E4). Editing one Amharic line regenerated one narration file, while the other 9 stayed byte-for-byte identical (checked with md5, FAILURES.md). The film stage always re-renders, since it only runs FFmpeg.

## Failure handling

| Failure | Handling | Where |
|---|---|---|
| Invalid storyboard | Rejected before any call, with the path and message for each error | `storyboard.py` |
| 429 / 5xx / dropped connection | Up to 4 tries with backoff, honouring `Retry-After`, but never waiting more than 30 s (a quota 429 once hung a run for 5+ min) | `common/http.py` |
| A Gemini model overloaded or over quota | Move to the next model in the chain. Every attempt is logged | `common/gemini.py` |
| Translator fails or returns bad JSON | Fall back from Addis AI to Gemini 2.5 Flash | `script.py` |
| Video call fails | Make a Ken Burns push-in on the keyframe, so the film always has a picture. A rerun retries the real clip, because the fallback file has a different name | `shots.py` |
| Clip shorter than its narration | **Refused before spending money**, with the `clip_s` to use. Assembly slows clips by no more than 0.8× | `shots.length_problems`, `assemble.fit_clip` |
| Too many parallel video jobs | 2 at a time (WaveSpeed returned 429 "Concurrency" at 4) | `shots.PARALLEL_JOBS` |
| A stage missing its inputs | Clear error naming the stage to run first | every stage |

## Timing and sound

The narration sets the clock. `assemble.build_timeline` places each line after a 0.3 s lead-in, with 0.35 s between lines and a 0.6 s tail. A shot lasts `duration_s` or longer, whichever its lines need. Subtitles, clip fitting, the music length and both films all come from this one timeline.

Sound (`assemble.render_narration_track`, `duck_mix`, `film.normalize_loudness`):
1. The voice goes to −16 LUFS and the music to −26 LUFS, so balance decisions are creative ones, not repairs.
2. The music is ducked under the voice with `sidechaincompress` (threshold 0.02, ratio 6, attack 300 ms, release 1500 ms) and fades out over the last 2 s.
3. A two-pass `loudnorm` brings the mix to −14 LUFS, with a true-peak target of −1.5 dB. The −1.0 target measured −0.8 after AAC encoding.

## Provenance

`runs.jsonl` has one line per model call: timestamp, stage, provider, model, params, seed, latency, list price, billed cost, status, error and output path. Two things are built from it:
- `make costs` writes COSTS.md.
- `endcard.credit_lines` looks up, for every file in the finished film, which model wrote it. The end card can only name models that were really used. That is why it lists both Gemini TTS models: the teacher's line came from the Flash-Lite fallback.

## Tests

`make test` runs 13 tests, aimed at the logic that would silently ruin a film or waste money:
- schema typos, duplicate ids and refusing to save an invalid storyboard;
- the cache hash;
- the timeline, subtitle splitting and clip fitting;
- the clip-length guard;
- which clip the film uses;
- a reference change regenerating only the keyframes that show that character.
