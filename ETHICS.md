# Ethics: consent, licences, labelling

## Consent

**No real person is shown or voiced in this film.**

- **The dad is an invented character ("a dad"), not my father.** The first idea was "my dad narrating his own journey". On 2026-11-26 I chose an invented dad instead (DESIGN.md, Decisions). His character description is generic: an Ethiopian man of about 45 with a gabi and a greying beard. It was never based on a photo of anyone.
- **The kid, the young dad and the teacher are invented too.** No photo of a real person was given to any model. The only images sent were our own generated keyframes and references.
- **The voices are stock Gemini TTS voices** (`Algenib`, `Puck`, `Kore`). No voice was cloned, and no recording of a real person was uploaded anywhere.
- **The story is a shared joke, not one family's private history.** It is the "when I was your age, I walked to school…" story many Ethiopian parents tell. No real names, villages or private family details appear in any prompt.
- **User-test viewers.** Friends watched the cuts and gave reactions. Only their names and words are recorded, in DESIGN.md, with the director's OK. They do not appear in the film.

## Style and other people's work

- Prompts describe qualities ("minimal hand-drawn doodle", "sleepy half-closed eyes", "flat sage green") and never name an artist or studio.
- Style B came from a reference image the director liked. That image was **not** given to any model. We wrote its qualities down in our own words (EXPERIMENTS.md E5).

## Licences

| Part | Model / asset | Licence or terms | Notes |
|---|---|---|---|
| Keyframes | FLUX.2 klein 4B (Black Forest Labs), via Cloudflare Workers AI | Weights: Apache 2.0 | The 9B klein is non-commercial. We used the 4B. |
| Video (film) | Grok Imagine Video 1.5 Lite (xAI), via OpenRouter | Provider terms (xAI, OpenRouter) | Closed model. We did not find an output licence statement in the docs we read. **Not verified.** |
| Video (drafts, experiments) | Wan 2.2 (Alibaba), via WaveSpeed | Apache 2.0, no rights claimed on outputs | Not in the final film. |
| Music | ACE-Step 1.5, via WaveSpeed | Model: MIT | The challenge brief says ACE-Step 1.5 outputs may be used commercially. The repo asks users to disclose AI use, which we do. |
| Narration | Gemini 3.8 Flash TTS / Flash-Lite TTS (Google) | Gemini API terms: Google does not claim ownership of outputs | **Free-tier prompts and outputs may be reviewed by humans and used to improve Google products**, so we sent no private details. |
| Translation | Addis AI chat (`Addis-፩-አሌፍ`); experiments with GLM 5.3 Flash, Gemini, Gemma, Claude Sonnet | Provider terms | Addis AI's output terms were not checked. |
| End-card font | Ubuntu Bold and Light | Ubuntu Font Licence 1.0 (`assets/fonts/UBUNTU-FONT-LICENCE.txt`) | Bundled so a fresh clone renders the same card. |
| Assembly | FFmpeg | LGPL/GPL tool, used as a program | No AI. |

## Labelling plan

1. **In the film:** a 3 s end card, "Made with AI", lists which model made each part. The list is read from `runs.jsonl` for the exact files in the film (`pipeline/endcard.py`), so it cannot name a model that wasn't used.
2. **On the platform:** the film is posted on LinkedIn. Any AI-content label the platform offers is switched on when posting.
3. **In the post:** the text says the film was made with AI models, and how.
4. **Provenance metadata: an honest gap.** Our FFmpeg assembly re-encodes every clip. Any C2PA manifest or embedded provenance metadata in the provider outputs **does not survive** into the final MP4. Some audio or video watermarks (such as SynthID) may survive re-encoding, but we did not verify which of our inputs carry one. The end card and the platform label are how we disclose AI use.

## Private data

No names, addresses, photos or voices of family members were sent to any API. API keys live only in `.env`, which `.gitignore` excludes from git. `.env.example` lists the variable names with no values.
