# Failures

What broke, what we tried, and what fixed it. Newest first. Evidence lives in `runs.jsonl`.

## 2026-11-26: Video clips were 21 s shorter than the narration

**What happened.** All 8 clips were made at 8 s (`clip_s: 8`), a length chosen when Wan was the engine, since Wan only makes 5 or 8 s clips. But shot lengths come from the Amharic narration, which stretched 6 of 8 shots to 9.5–12.8 s. The clips added up to 64 s against 85 s of narration. The director noticed it while watching. No check in the code caught it, and $2.00 of Grok clips had already been made at the wrong length.

**Why it was possible.** The shots stage never looked at the narration. `clip_s` was a fixed guess in the storyboard, and nothing compared it with the real shot length.

**Fix, so it can't happen silently again.**
- `assemble.fit_clip(clip_s, shot_s)` is one rule for filling a shot: trim a long clip, slow a slightly short one to no less than `MIN_CLIP_SPEED = 0.8`, and call anything shorter `too_short`.
- `assemble.shot_lengths()` gives the final length of every shot from the narration files.
- `shots.length_problems()` runs **before any money is spent**. It refuses to render if a clip is too short for its narration, or if the engine can't make that length (Wan: 5 or 8 s; Grok: 1–15 s). It suggests the `clip_s` to use. On its first real run it caught a shot we had missed: s05 needed 10.03 s, so an 8 s clip would have played at 0.797×.
- The schema now allows `clip_s` from 1 to 15.

**Result.** Re-rendered s01, s04, s07 and s08 at 13 s and s05 at 10 s, $1.91. All 8 clips now cover their shots. Seven are trimmed; s06 (8 s clip, 9.5 s shot) is slowed to 0.846×.

## 2026-11-26: WaveSpeed refused 4 clips at once (HTTP 429 "Concurrency")

**What happened.** The shots stage sent 4 Wan 2.2 jobs in parallel. 4 of 8 shots (s01, s02, s07, s08) failed with HTTP 429 and a "Concurrency" message. The account allows fewer jobs at the same time than we sent. Our retry (4 tries, 2–8 s apart) was too short to wait for a free slot.

**What saved the run.** The Ken Burns fallback in `pipeline/shots.py` made a slow push-in on the keyframe for each failed shot, so the film still had a picture for all 8 shots. Failed calls are logged with `billed_usd: 0`.

**Fix.** `PARALLEL_JOBS = 2`. The rerun only retried the 4 shots without a real Wan clip, because the fallback file has a different name from the Wan clip, and all 4 worked. Total cost for 8 draft clips: 8 × $0.08 (estimated; 8 s at 480p, assuming the 5 s price scales with length).

## 2026-11-26: Narration rerun hung on a Gemini TTS rate limit

**What happened.** Regenerating one changed line (the teacher's) hung for more than 5 minutes with no new line in `runs.jsonl`. Earlier calls that morning had already hit HTTP 429 ("Rate limit exceeded") on `gemini-3.8-flash-tts`.

**Cause (likely).** `request_with_retry` obeyed the `Retry-After` header with no upper limit. A quota-type 429 can ask for a wait of many minutes. We did not capture the header, so this is our best explanation, not a proven one.

**Fix.** `MAX_RETRY_WAIT_S = 30` in `pipeline/common/http.py`. A longer requested wait now fails at once, so `interact_with_fallback` moves to the next model. The rerun finished in about 20 s.

**Side effect.** With `gemini-3.8-flash-tts` rate-limited, the teacher's line came from `gemini-3.8-flash-lite-tts` both times. The native speaker found its pronunciation weaker. The film keeps it for now. A retry on the main model, or Addis AI TTS, is the fix if user tests flag it.

**Evidence that caching held.** Before the rerun we saved an md5 of every narration file. After it, only the 3 lines whose text changed (s05, s06, s08 teacher) had new files, and all 7 old files were byte-for-byte unchanged.

## 2026-11-26: Addis AI chat reply was not where the docs said

**What happened.** The Addis AI docs show `/chat_generate` returning `response_text` at the top level. The live API wraps it: `{"status": "success", "data": {"response_text": ...}}`. Our client raised "no response_text" on a successful call. The translation in that reply was lost, because the log only keeps the first 300 characters of an error.

**Fix.** `pipeline/common/addis.py` unwraps `data` when it is there, and we reran the one call (5 s, about 1 ETB).

**Lesson.** Read one real response before trusting a provider's docs. The smoke test is the place for that.

## 2026-11-26: GLM 5.3 Flash failed on the full script

**What happened.** GLM translated one sentence well (EXPERIMENTS.md E1), so it became the main translator. On the full 10-line script it produced poor Amharic: wrong words (`ሽቦ` "wire" for string, `ጋሻ` "shield" for hill, `ላባ` "feather" for lava), words that are not Amharic (`እንደማርካ`, `ጆሌሁ`), and nonsense such as `እንጁቡ ረቡብ`. The call took 178 s. A native speaker called it "very bad".

**What we tried.** Four cheap models with the same prompt (E2). Gemini 2.5 Flash was clearly best. Gemma 3 27B was worse than GLM, mixing in other scripts.

**Fix.** Switched `TRANSLATOR_MODEL` to `google/gemini-2.5-flash` and replaced every line's `spoken` text with its output, plus one hand fix (`ሲሚን` → `ሰሜን`).

## 2026-11-25: Gemini Flash-Lite mistranslated "grandmother" into Amharic

**What happened.** In the smoke test we asked `gemini-3.5-flash-lite` to translate "My grandmother walked to the market every Saturday." into Amharic. It returned `ቅድመ አባቴ በየቅዳሜ ወደ ገበያ ትጓዝ ነበር።`. `ቅድመ አባቴ` means "my forefather", not "my grandmother" (`አያቴ`). The verb `ትጓዝ` is feminine, so the sentence also mixes genders. A native speaker confirmed the error.

**Why it matters.** The film is narrated in Amharic. A wrong kinship word changes who the story is about, and English-speaking reviewers would not notice it.

**What we did.** Noted it. Flash-Lite was only used because `gemini-3.8-flash` was overloaded (see below).

**Fix.** Tried a different model on the same prompt (EXPERIMENTS.md E1). `z-ai/glm-5.3-flash` via OpenRouter got it right, and a native speaker confirmed it. GLM is now the main translator. A native speaker still listens once to the radio cut, where a wrong word would be heard.

## 2026-11-25: `gemini-3.8-flash` overloaded (HTTP 503) on every try

**What happened.** Three smoke-test runs in a row failed on `gemini-3.8-flash`. Two returned HTTP 503 ("currently experiencing high demand"). One timed out after 4 retries (about 278 s). TTS on the same key worked, so the key was fine.

**What we tried.**
1. Retried with backoff (4 attempts). Still 503 or timeout.
2. Called the model directly through the Interactions API with curl. Still 503 after 56 s.
3. Called `gemini-3.5-flash-lite` instead. It answered in about 20 s.

**Fix.** `pipeline/common/gemini.py` now tries models in order and moves on when one returns 429, 503 or times out:
- text: `gemini-3.8-flash` → `gemini-3.5-flash-lite`
- TTS: `gemini-3.8-flash-tts` → `gemini-3.8-flash-lite-tts` → `gemini-2.5-flash-preview-tts` (idea from a colleague on Slack)

Each attempt is logged, so `runs.jsonl` shows the failed call and the fallback that worked.

**Trade-off.** A fallback model can be worse. The mistranslation above came from the fallback. Flash-Lite TTS has no Tigrinya or Somali, and the 2.5 TTS model is deprecated from 2026-12-01.
