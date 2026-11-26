# When I Was Your Age: report

**Samuel Birhanu** · B2W0: AI-Content Generation · 26 November 2026

| | |
|---|---|
| Repository | <https://github.com/sami-bre/videomaker> |
| Live app | <https://videomaker.samibre.dev> |
| Film, 9:16 | <https://videomaker.samibre.dev/files/example/outputs/film/film-9x16.mp4> |
| Film, 16:9 | <https://videomaker.samibre.dev/files/example/outputs/film/film-16x9.mp4> |
| Run it | `git clone … && make setup && make film` |

**In numbers:** an 88-second film in Amharic with English subtitles, 8 shots, 10 narration lines. It cost **$2.69** in model calls, and **$4.96** for everything I tried along the way, including failures (`COSTS.md`, built from 117 logged calls in `runs.jsonl`). 10 experiments, 7 recorded failures, 2 user tests with 11 people, 20 automated tests.

## 1. What I set out to make, and for whom

Every Ethiopian kid has heard it: *"When I was your age, I walked to school…"* My film takes that story to its comic extreme. A dad tells his son how he got to school every day. He crossed the Blue Nile past a hungry crocodile, tiptoed under an elephant in Chebera Churchura, climbed the Simien cliffs past bored geladas, and hopped across the lava of Erta Ale. He finally arrives, soaked and smoking, and the teacher says: **"ዛሬም እንደገና አረፈድክ!"** ("You're late again!").

**The audience** is Ethiopian friends my age, in their 20s, who grew up hearing this story from their own parents. **The intent**, written in `DESIGN.md` before I generated anything: they should *laugh in recognition* ("my dad says exactly this") and *feel a little respect*, because under the exaggeration many of our parents really did walk very far to school.

Two early decisions shaped everything:
- **The narrator is "a dad", an invented character, not my father.** My first idea was my own dad's story. A real person shown or voiced needs a consent record, and the shared, recognisable story works better without one family's details (`ETHICS.md`).
- **A cartoon, not realism.** Lava and crocodiles read as a joke in a doodle and as fake in a realistic shot. A simple drawn character is also easier to keep consistent across shots.

I also set out to build the pipeline **as software other people can use**, not a one-off script for one film. That choice drove the architecture: one `storyboard.json` contract, a schema checked on every load, and outputs named by a hash of their inputs, so a new film needs a new storyboard, not new code.

## 2. What I learned from my audience

**User test 1, the radio cut** (narration over a placeholder drone, no pictures). Four friends listened. Three gave praise: Mekdes ("send it to me once you have the video"), Paul ("Soo funny! Even the lava 😄") and Yonas ("You should post this somewhere!"). Praise told me the comedy worked from the voice alone, but not what to improve.

**Yusuf's comment changed the script:**

> "Made me laugh so hard. You know, but it should say *znjerowochu yayugn neber* (ዝንጀሮዎቹ ያዩኝ ነበር, 'the monkeys used to watch me'), not *znjerowochu ayugn* (ዝንጀሮዎቹ አዩኝ, 'the monkeys watched me')."

He was right, and it was a deeper point than one word. The dad is describing a **routine**, something he went through every school day, not one trip. In English the difference is subtle; in Amharic the verb form makes it obvious. A one-time past turns the story into an anecdote; the past habitual turns it into a life. It is also what makes the punchline land: the teacher says "late *again*" because this happened every day.

The fix went into the storyboard, not just one line. The English moved to "would" / "used to", and I added `translation_notes` asking the translator for the past habitual. The gelada line in shot s06 now says `ዝም ብለው ያዩኝ ነበር`. Because only lines whose English changed are retranslated, and narration is cached per line, the change cost one translation call and a few voice lines.

**User test 2, the near-final cut.** I posted the 16:9 film in my cohort's Slack thread. It got 13 replies in about 20 minutes and 27 🔥 reactions. Two replies matched the intent exactly: Robel, *"It turns out every parent has a similar story!"* (recognition), and Eyosiyas, *"the exaggeration 😂👌"* (the escalation is the joke). Haylemichael found a joke I hadn't planned: *"he was a tourist not a student 🤣"*. The commute is a tour of Ethiopia's famous sights. Nothing in the storyboard changed after this test, because nobody was confused and nothing was flagged as long.

**What I'd do differently:** public replies in a group thread are short and kind. They show that the film lands, not where it is weak. Next time I would ask two or three people privately: where did you laugh, and where did you look away?

## 3. The hardest problem: Amharic that sounds right

Generating pictures and clips was the easy part. The hardest problem was narration that a native speaker would accept. It took five rounds, and each round's evidence is in `EXPERIMENTS.md` and `FAILURES.md`:

1. **Gemini Flash-Lite mistranslated "grandmother"** as "my forefather" with mixed gender (E1, FAILURES.md).
2. **GLM 5.3 Flash fixed that one sentence**, so I picked it. On the full script it was poor: "wire" for string, "shield" for hill, "feather" for lava, and words that are not Amharic (E2). **One sentence picked the wrong model.**
3. **Gemini 2.5 Flash was correct, but dull** once the script used the habitual: 16 of its sentences ended in `ነበር` (E3).
4. **Addis AI**, an Ethiopian provider, varied the sentence endings (12 `ነበር`), used the right word for gelada (`ጭላዳ`), and made the teacher sound correct. Its line-by-line endpoint, without the story as context, made real errors, such as "Black Nile" (E3). **Context mattered more than the model.**
5. **The teacher's line still sounded wrong** when voiced. I assumed the cheaper fallback voice model was to blame. But the same model read a corrected text (`አርፈድክ` → `አረፈድክ`) well. The problem was the spelling, not the model (E10).

**How I solved it:**
- Every translation call gets the whole script plus story-specific `translation_notes` (tense, spellings of place names), not one line at a time.
- Addis AI is the main translator for Amharic, with Gemini as the fallback.
- **A hand edit by a native speaker is kept.** The storyboard records which English each `spoken` line was translated from (`spoken_from_en`), so a line is retranslated only when its English changes. My fix `በስብሼ እና ጨሼ` ("soaked and smoking") in s08 survives every rerun.
- Narration falls back across three Gemini voice models, and retries never wait more than 30 s. A rate limit once hung a run for 5 minutes (FAILURES.md).

The lesson: for a language with less training data, the native speaker's ear is the final test, and the pipeline has to make that ear cheap to use. That means a radio cut, line-level caching, and hand edits that are never overwritten.

**A close second** was a mistake I only caught by watching: the 8 video clips added up to 64 s against 85 s of narration (FAILURES.md). Slowing a clip to 0.8× still looked natural, so I re-rendered only the 5 shots that couldn't stretch, for $1.91. I also added a check that measures each shot against its narration *before* any clip is paid for. On its first run it caught a shot I had missed by eye (E9).

## 4. Suggested practices, tested honestly

**One that beat my instinct: the narration-only radio cut.** My instinct was to start with pictures, because that's the exciting part. The radio cut felt like a step backwards. But it found the most important fix in the whole film, Yusuf's habitual tense. It also checked the comedy for free: three of four listeners laughed from the voice alone.

**One that didn't work for me: the suggested translation models.** The suggested stack lists Gemini Flash for translation, and Flash-Lite for bulk calls. For Amharic it fell short every time I tested it: Flash-Lite got a kinship word wrong (E1), Gemini 3.8 Flash returned HTTP 503 "high demand" on every try (FAILURES.md), and Gemini 2.5 Flash was correct but flat (E3). What worked was a local provider built for Ethiopian languages, given the whole story as context. Gemini stayed useful, as the fallback and for the voices, but not as the translator.

## 5. Beyond the floor

- **The pipeline as a web app anyone can use: <https://videomaker.samibre.dev>.** One page shows the film, then a studio below it, where anyone can remix the film or start blank. People edit shots in forms, checked against the schema as they type. Each step shows what it will make, what it will reuse, and the rough cost *before* you click. Runs stream their log live.
- **Bring your own keys, no accounts.** Each project lives at an unguessable link. Keys stay in the browser and go only into that run's process, and a test checks they never reach a log. A remix shares the example's generated files by hard link, so changing one line costs one voice line, not $2.70.
- **Steps that refuse to waste money.** Each step checks that what it needs exists ("Run Voice first: 1 voice line missing") and that every clip is long enough for its narration, before calling a paid model.
- **Packaging.** A Docker image (cut from 1.42 GB to 862 MB by moving the example's files onto a data volume), a how-to guide at `/docs/`, and 20 tests on the logic that would silently ruin a film, waste money or leak a key.
- **An Ethiopian provider benchmarked against a frontier model** (Addis AI vs Gemini, E3). I also compared an open-weight video model with a frontier one on the same shot, with measured cost and latency: Wan 2.2 vs Grok Imagine (E6). Grok's style drift was then fixed with one storyboard field, `motion_style` (E7).
- **Honest credits.** The end card lists which model made each part, read from `runs.jsonl` for the exact files in the film, so it cannot name a model that wasn't used.

## 6. What I would build next

1. **Test Addis AI's own text-to-speech** against Gemini's for Amharic voices. The translation test showed a local provider can beat a general model on Amharic.
2. **Takes, not overwrites.** In the studio, keep every version of a shot side by side, and let the user pick one, the way the music step already works.
3. **Private feedback in the app.** A link where a viewer marks the moment they laughed or got bored, so user tests give timestamps, not just praise.
4. **Keep provenance metadata.** The FFmpeg edit re-encodes every clip and drops any C2PA data from the providers (ETHICS.md). The finished film should carry its own.
