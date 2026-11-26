# Experiments

Each entry: hypothesis → change → result → decision. Evidence lives in `runs.jsonl`.

## E1. GLM 5.3 Flash vs Gemini 3.5 Flash-Lite for English → Amharic (2026-11-25)

**Hypothesis.** Flash-Lite's "grandmother" mistake (see FAILURES.md) is a weakness of that model, not of LLM translation into Amharic in general. A different model given the same prompt will get the kinship word right.

**Change.** Same prompt, same seed (42), different model: `z-ai/glm-5.3-flash` through OpenRouter instead of `gemini-3.5-flash-lite`.

Prompt: "Translate into Amharic, reply with the translation only: My grandmother walked to the market every Saturday."

**Result.**

| Model | Output | Correct? | Latency | Cost |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` | ቅድመ አባቴ በየቅዳሜ ወደ ገበያ ትጓዝ ነበር። | No: "my forefather", mixed gender | 19.8 s | free tier |
| `z-ai/glm-5.3-flash` | ሴት አያቴ በየቅዳሜው በእግር ወደ ገበያ ትሄድ ነበር። | Yes (confirmed by a native speaker) | 10.9 s | $0.00116 |

GLM uses `አያቴ` (grandparent) with `ሴት` (female), and keeps the verb feminine (`ትሄድ`). It also keeps "walked" as `በእግር` ("on foot"), which Flash-Lite dropped.

**Caveat.** One sentence is not a benchmark. It shows the error is not shared by every model. It does not show GLM is better in general.

**Decision (later reversed by E2).** Use GLM 5.3 Flash as the main English → Amharic translator, with Gemini as the fallback. It costs about a tenth of a cent per sentence, which is fine for about 15 narration lines. Because one sentence is a small sample, the real narration lines still get one native-speaker read in the radio cut (user test 1), not a line-by-line check before TTS.

## E2. Cheap models on the full script, English → Amharic (2026-11-26)

**Hypothesis.** E1 tested one sentence. On the full 10-line script, GLM 5.3 Flash will stay good, and the cheap Gemini and Gemma models will be close to it.

**Result for GLM.** The hypothesis was wrong. GLM's full-script translation was poor (see FAILURES.md): wrong words such as `ሽቦ` (wire) for string, `ጋሻ` (shield) for hill and `ላባ` (feather) for lava, and words that are not Amharic. It also took 178 s.

**Change.** Same prompt (`pipeline/script.py: build_prompt`, the whole script as context), sent through OpenRouter to four cheap models. Outputs are in `outputs/script/compare-*.json`. A native speaker judged them.

| Model | Price per 1M (in / out) | Latency | Cost | Verdict |
|---|---|---|---|---|
| `google/gemini-2.5-flash` | $0.30 / $2.50 | 4.1 s | $0.0012 | **Chosen.** Right words for string, hill, crocodile, lava, jumped. Natural teacher line `እንደገና አርፈድክ!`. Minor: `ሲሚን` instead of `ሰሜን` (fixed by hand), literal `ሰማያዊ አባይ`. |
| `google/gemini-3.1-flash-lite` | $0.25 / $1.50 | 5.6 s | $0.0008 | Good words, but s02 in present tense, and s07 loses the rocks. |
| `google/gemma-4-31b-it` | $0.20 / $0.40 | 7.6 s | $0.0003 | Two real errors: a Cyrillic letter in s01, and `አላለፍኩም` ("I did not cross") in s04. The `:free` tier returned HTTP 429. |
| `google/gemma-3-27b-it` | $0.08 / $0.16 | 16.9 s | $0.0001 | Unusable: mixes Chinese, Korean, English and French into the Amharic. |
| `z-ai/glm-5.3-flash` (E1 pick) | $0.15 / $0.50 | 178 s | $0.0080 | Poor, see above. |

An earlier side run of `anthropic/claude-sonnet-5.5` ($0.008) was stopped and not judged. Expensive models are out of scope by choice.

**Lesson.** A one-sentence test (E1) picked the wrong model. The full script, with real place names and slang, is the test that counts.

**Decision (later replaced by E3).** `TRANSLATOR_MODEL = "google/gemini-2.5-flash"` in `pipeline/script.py`. Risk: Google is deprecating 2.5 models on its own API from 2026-12-01. For the reusable tool, `gemini-3.1-flash-lite` is the next choice.

## E3. Addis AI (Ethiopian provider) vs Gemini 2.5 Flash (2026-11-26)

**Why.** After the script was rewritten as a routine ("used to", see `translation_notes`), Gemini 2.5 Flash's Amharic felt dull to the native speaker: almost every sentence ended in `ነበር`.

**Hypothesis.** A provider built for Ethiopian languages will write more natural spoken Amharic than a general model.

**Change.** Two Addis AI endpoints on the same script:
- `/chat_generate` (their LLM, `Addis-፩-አሌፍ`), given the same prompt as E2 (`build_prompt`: the whole script, the routine note, the spelling notes).
- `/translate`, one line at a time, so no story context.

Outputs are in `outputs/script/compare-addis-*.json`.

**Result.**

| Translator | `ነበር`/`ነበረ` count | Latency | Cost | Notes |
|---|---|---|---|---|
| Gemini 2.5 Flash (E2 pick) | 16 | 2–4 s | ~$0.001 | Correct but repetitive. `ጀላዳ` for gelada. `እየተንቦገቦገኩ` ("blazing") in s08. Feminine teacher (`ትለኝ`). |
| **Addis chat** | 12 | 5.2 s | 2,269 in + 477 out tokens ≈ 1.06 ETB | **Chosen.** Varies the endings (`-ና` joins, `ነው የምሄደው`, `ይኖራል`, `…እንጂ`). Correct `ጭላዳ`. Respectful, gender-neutral teacher (`ይሉኝ`). |
| Addis translate | 10 | ~2 s per line | ~200 tokens per line | Real errors without context: `ጥቁር አባይ` ("Black Nile"), "Churchura" left in English, `ሲሚን`, `እየተንፋፋሁ` ("panting"). |

**Lesson.** Story context matters more than a translation-only model. The same provider was good with the full prompt and wrong line by line. A raw count of `ነበር` is a rough measure of repetition, but the native speaker's read decided it.

**Decision.** The script stage now uses Addis AI chat for Amharic and Afaan Oromo, with `google/gemini-2.5-flash` on OpenRouter as the fallback. Its output is in `storyboard.json`, with one hand edit by the native speaker in s08: `ረጥቤና ጭስ እያወጣሁ` → `በስብሼ እና ጨሼ` ("soaked and smoking").

## E4. Reference sheet before keyframes: does the boy stay the same? (2026-11-26)

**Hypothesis.** Generating one reference image per character first, then passing it as `input_image_N` to every keyframe (Cloudflare `flux-2-klein-4b`, up to 4 references), with the same style block and character description in every prompt, keeps the young dad recognisably the same across 7 different places.

**Change.** `pipeline/keyframes.py`: 4 character references (1024×1024, shrunk to 496×496 because Cloudflare needs references under 512×512), then 8 keyframes at 1280×720, each conditioned on the references of the characters listed in the shot. Seeds are fixed in the storyboard (101–108).

**Result.**
- **Young dad, s02–s08: consistent.** Same curly hair, light-blue shirt, khaki shorts, bare feet, string-tied books in all 7 shots, from village to lava lake.
- **Dad reference: failed at first.** His description began "the same boy grown up…", and the model drew a child in a green shirt. In s01 that leaked: the dad looked generic, not Ethiopian, and the kid wore the wrong clothes. Rewriting it as "an Ethiopian man of about 45…" fixed both.
- **Smaller misses, left for now:** in s04 the river is knee-deep, not chest-deep. In s06 the geladas look like generic red-chested monkeys, and the boy stands instead of climbing. In s08 the teacher smiles instead of looking stern.

**Cost.** 14 image calls, all inside Cloudflare's free daily allowance. List-price equivalent ≈ $0.002 each (in `runs.jsonl`).

**Lesson.** The reference sheet works, but a description is read literally. A phrase that relates one character to another ("the same boy grown up") pulls in the wrong one. Each description must stand alone.

**Caching check.** After the dad fix, the stage regenerated exactly 2 images (the dad reference and s01, the only shot he is in). The other 10 were cached, because each keyframe's cache key includes the bytes of its reference images.

## E5. Style B: doodle stick figures with kuncho and gabi (2026-11-26)

**Why.** Style A (E4) was consistent but generic. The characters could have been from anywhere. The director wanted a specific doodle look (thin black ink stick figures, sleepy half-closed eyes, flat sage background) and Ethiopian markers: the young dad in a **kuncho** (shaved head with one tuft above the forehead, a rural boys' style) and the dad in a **gabi** (thick white handwoven cotton shawl).

Style A is kept for comparison in `outputs/keyframes/compare/style-a-*` (contact sheets plus the storyboard that made them).

**B, first try** (`compare/style-b-*`). Only the style block and character descriptions changed.
- Kuncho and gabi read clearly. The boy's deadpan sleepy face is funnier than A's cheerful generic boy.
- **The reference pose took over.** The boy stood facing the camera in all 7 flashback shots. He stood *on* the river instead of wading, and stood next to the cliff instead of climbing.
- **Style drifted outside the boy.** s01 came out semi-realistic. s03 and s07 had rich painted backgrounds.
- **s08 lost the teacher entirely.**
- The faces were white line art.

**B, second try** (`compare/style-b2-*`). Hypothesis: the reference images were pulling their standing pose into every shot, and a loose style block let backgrounds fall back to the model's default rich look. Changes:
1. `keyframe_prompt` now puts the action first and adds a rule: "use the reference images only for how each character looks… draw their pose and action exactly as described here". The style block moved to the end.
2. Every `image_prompt` was rewritten to lead with a pose verb and a camera side ("Seen from the side, the boy climbs…").
3. The style block now says every person is a stick figure, with flat warm-brown skin, and bans detailed or painted scenery.
4. s08 lists the boy first and puts him in front; the teacher is in the doorway behind.

**Result.** The style holds in all 8 shots, s01 included. The boy wades (s04), passes the elephant (s05), climbs past the geladas (s06) and leaps over the lava (s07). s08 shows him dripping and smoking in front of a glaring teacher. It took 2 rounds (13 images) plus 1 retry of s08 (the first try put the teacher in front and the boy tiny in the doorway). All were free (Cloudflare daily allowance).

**Remaining.** The boy is shirtless in every shot (consistent, so we kept it). The landmarks are less recognisable in the flat style than in A. The Simien peaks and the Nile now rely on the narration.

**Lesson.** With reference-conditioned image models, a neutral standing reference pose is "sticky". Writing the action first, and telling the model the reference is for looks only, broke it. **Decision:** style B (second try) is the film's look.

## E6. Wan 2.2 (WaveSpeed) vs Grok Imagine 1.5 Lite (OpenRouter) on the lava shot (2026-11-26)

**Why.** WaveSpeed's $1 free credit is almost spent (about $0.36 left), and none of the researched video services has a real free tier. Grok Imagine Lite runs on the OpenRouter key we already have.

**Hypothesis.** Grok will animate s07 (the boy jumping across the lava) at least as well as Wan, at an acceptable price for 720p finals.

**Change.** Same keyframe, same `motion_prompt`, 8 s. Wan: `i2v-480p-ultra-fast` (draft). Grok: `x-ai/grok-imagine-video-1.5-lite` at 720p, `generate_audio: false`. Frames compared at 0.5, 2.5, 4.6 and 7.5 s: `outputs/shots/compare-s07-wan-vs-grok.png`.

**Result.**

| | Wan 2.2, 480p | Grok Imagine Lite, 720p |
|---|---|---|
| Cost | ~$0.08 (estimated) | $0.25 (reported by OpenRouter) |
| Time | ~70 s | 47 s |
| Output | 832×464, 30 fps | 1280×720, 24 fps |
| Motion | The boy runs in place between two rocks. Smoke puffs. The camera holds still, as asked. | More cinematic: the camera moves, the boy turns away and steps onto a rock, and the lava starts bubbling. |
| Style | Stays flat and doodle-like to the end. | Drifts from the second half on: glowing particles, soft smoke clouds, shaded lava. It looks less like our style. |
| Character | Stays big, centred, facing us. | Gets smaller and turns his back, so we lose the deadpan face. |

**Lesson.** Grok gives richer motion and native 720p at 24 fps, but it ignored "Static camera" and pulled the picture toward its own realistic rendering. Wan followed the prompt and the style more closely. For a flat doodle film, keeping the style matters more than the extra motion.

## E7. A `motion_style` line stops Grok drifting from the doodle look (2026-11-26)

**Hypothesis.** In E6, Grok drifted toward its own rendered look (glow, particles, shading) and ignored "Static camera". If every motion prompt ends with an explicit instruction to keep the first frame's flat look, the drift will stop.

**Change.** A new storyboard field `motion_style`, added to every motion prompt by `pipeline/shots.py`: "Keep the exact flat 2D hand-drawn doodle look of the first frame for the whole clip… no glow, no particles, no shading, no 3D… Keep the characters the same size and facing the same way. The camera stays still unless the prompt asks it to move." The director chose Grok Imagine Lite at 720p for all 8 shots (`video_engine: "grok"`).

**Result.** All 8 shots succeeded on the first try. Time 36–56 s each, **$0.25 each, $2.00 total** (reported by OpenRouter as `usage.cost`). Review frames: `outputs/shots/review-grok-final.png`.
- **s07 re-rendered with the new line: the drift is gone.** It stays flat orange and black, with small doodle smoke puffs, and the boy stays the same size. Compare with E6's glowing, particle-filled second half.
- The style holds in all 8 shots. Motion is better than Wan's drafts: the dad leans over the kid (s01), the boy walks past the elephant (s05) and climbs past the geladas (s06), and s08 pushes in on his smug, dripping face.
- One artifact: in s04 the crocodile swims through the boy's legs at the end, where their outlines merge. It can be trimmed in the edit.

**Lesson.** Image-to-video models fall back to their default look over time. One fixed sentence, kept in the storyboard and added to every prompt, fixed it, just as the fixed style block did for keyframes (E5).

## E8. Choosing the score: three ACE-Step seeds under the narration (2026-11-26)

**Hypothesis.** With one fixed caption ("playful comic Ethiopian folk instrumental, krar and masinko with light kebero, sparse and quiet under a narrator…"), different seeds give different pieces. Choosing by ear *under the narration*, not on its own, picks the one that serves the film.

**Change.** `pipeline/music.py`: ACE-Step 1.5 on WaveSpeed, `[instrumental]`, 91 s (the whole film plus the end card), seeds 301, 302 and 303. About $0.027 each. Each candidate was mixed the way the film will be (`assemble.duck_mix`: music at −26 LUFS, sidechain-ducked under the voice with threshold 0.02, ratio 6, attack 300 ms, release 1500 ms, mix at −14 LUFS), giving `outputs/music/audition-seed*.m4a`. All three measured −14.3 LUFS, peak about −0.7 dB.

**Result.** The director chose **seed 301**: "mainly because the ending is good." The film ends on the teacher's line and then the end card, so a strong musical ending carries the punchline.

**Decision.** `music.chosen_seed: 301`, with `why_chosen` stored in the storyboard so the reason travels with the choice.
