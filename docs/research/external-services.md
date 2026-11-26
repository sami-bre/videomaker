# External services for the short-film pipeline

Checked on **2026-11-25**. Every price below comes from the provider's own page, docs or API on that date, unless it is in the "Could not verify" list. Prices change often. Re-check before you spend money.

The film: 60–90 s, about 10 shots of 5 s video, 10 keyframes plus 20 retries, about 200 words of narration, 3 music tracks of 90 s.

---

## Summary: what to use

| Stage | Pick (cheapest hosted that works) | Backup | Cost for one film |
|---|---|---|---|
| Text LLM (script, storyboard, Amharic) | Gemini API free tier, `gemini-3.8-flash` | OpenRouter (one key for many models; takes USDC crypto) | $0 |
| TTS narration (Amharic) | Gemini API free tier, `gemini-3.8-flash-tts` | Azure Speech free tier F0, `am-ET-MekdesNeural` / `am-ET-AmehaNeural` | $0 |
| Keyframes with reference images | Cloudflare Workers AI free tier, `@cf/black-forest-labs/flux-2-klein-4b` (up to 4 reference images) | Black Forest Labs API, FLUX.2 [klein] 4B ($0.014 first MP) | $0 (backup about $0.45) |
| Image-to-video | WaveSpeed, Wan 2.2 I2V 720p Ultra Fast ($0.10 per 5 s clip) | Alibaba Model Studio `wan2.2-i2v-flash` ($0.015/s at 480p, $0.036/s at 720p), or Grok Imagine Video 1.5 Lite on fal/OpenRouter ($0.03/s at 720p) | about $1–2 |
| Music | ACE-Step 1.5 on WaveSpeed ($0.0003/s) or ACE-Step on fal ($0.0002/s) | Stable Audio API ($0.08 per track) or Lyria 3.5 on Gemini API ($0.08 per song) | under $0.10 |

**Rough total for one film**

- **Minimum** (10 clips at 480p, no video retries): video $0.50 + music $0.08 = **about $0.60**. Everything else is on free tiers.
- **Realistic** (10 shots × 2 tries = 20 clips at 720p): video $2.00 + music $0.08 = **about $2.10**.
- **Backup stack** (Alibaba 720p video ×20 = $3.60, BFL keyframes ×30 = $0.45, Lyria ×3 = $0.24, paid Gemini TTS ≈ $0.05): **about $4.35**.

My math, from the prices in the tables below. The real cash cost is often the **minimum top-up**, not the usage. Gemini paid billing has a $5 minimum prepay. OpenRouter adds a 5.5% fee ($0.80 minimum) on card top-ups. WaveSpeed gives $1 free credit to new accounts.

**Two notes on the challenge brief's stack.**

- Mostly still right. Gemini 3.8 Flash and 3.8 Flash TTS are free. Cloudflare FLUX.2 klein and FLUX.1 schnell fit in the free daily quota. Nano Banana, Gemini Omni Flash video and Lyria 3.5 are paid only.
- Corrections. There is no "3.8 Flash-Lite" *text* model. The newest Flash-Lite text model is `gemini-3.5-flash-lite` (`gemini-3.8-flash-lite-tts` is TTS only). Veo is not on the Gemini API price page, but Veo 3.1 / Fast / Lite still exist through OpenRouter (Google Vertex) and fal. HunyuanVideo 1.5 is "open weights" under a Tencent licence that does **not** apply in the EU, UK or South Korea. Free users no longer get Hugging Face Inference credits.

**For Ethiopia.** Ethiopia is on the supported list for the Gemini API and the OpenAI API. I could not confirm country support for most other providers (see "Could not verify"). If you have no international card, the best options are OpenRouter (takes USDC crypto) and WaveSpeed (takes PayPal, Alipay and others, "availability varies by region"). Gemini's free tier and Cloudflare's free tier need no payment to start.

---

## 1. Text LLM (script, storyboard, translation incl. Amharic)

| Provider | Model | Price (per 1M tokens in / out) | Free tier / limits | Ethiopia / payment | Output licence | Notes |
|---|---|---|---|---|---|---|
| Gemini API | `gemini-3.8-flash` | $0.75 / $3.75 until 2026-12-31, then $1.50 / $7.50 [g-price] | Free tier: "Free of charge" [g-price]. Exact RPM/RPD not published in docs, only in AI Studio [g-rate] | Ethiopia listed [g-regions]. Free tier needs no card. Paid needs a Cloud Billing payment method, prepay min $5 [g-billing] | Google "won't claim ownership" of output [g-terms] | Free-tier inputs/outputs may be read by human reviewers and used to improve Google products [g-terms]. Must be 18+ [g-terms] |
| Gemini API | `gemini-3.5-flash-lite` | $0.30 / $2.50 [g-price] | Free of charge [g-price] | same | same | Newest Flash-Lite *text* model. `gemini-2.5-flash` and `gemini-2.5-pro` are deprecated and re-route on 2026-12-01 [g-price] |
| OpenRouter | `:free` models, `openrouter/free` router | $0 for `:free` models | 20 RPM. 50 requests/day total if you bought under 10 credits, 1,000/day if you bought 10+ [or-limits] | Cards, AliPay, USDC crypto. Fee 5.5% (min $0.80) on cards, 5% on crypto [or-faq]. No country list in FAQ [or-faq] | Depends on the model | One key for text, image, video and TTS. I could not read the current list of free text models (see Could not verify) |
| Groq | `openai/gpt-oss-120b` | $0.15 / $0.60 [groq-models] | Free plan limits are only shown in your console. Developer plan: 30 RPM, 1K RPD for this model [groq-rate] | Not checked | gpt-oss is open weights | Very fast. No Amharic quality data |
| Groq | `openai/gpt-oss-20b` | $0.075 / $0.30 [groq-models] | as above [groq-rate] | Not checked | | |

**Judgement.** Use Gemini 3.8 Flash on the free tier. It is the only option here from a lab that also ships Amharic TTS, which suggests Amharic support, but I did not find a stated Amharic *text* quality claim, so test it. OpenRouter is the backup and the easiest way to pay from Ethiopia. Tell users of the pipeline that Gemini's free tier sends their prompts to human review, and that apps offered to EEA/UK/Swiss users must use paid tiers [g-terms].

[g-price]: https://aistudio.google.com/docs/pricing
[g-rate]: https://aistudio.google.com/docs/rate-limits
[g-regions]: https://aistudio.google.com/docs/available-regions
[g-billing]: https://aistudio.google.com/docs/billing
[g-terms]: https://aistudio.google.com/docs/terms
[or-limits]: https://openrouter.ai/docs/api-reference/limits
[or-faq]: https://openrouter.ai/docs/faq
[groq-models]: https://console.groq.com/docs/models
[groq-rate]: https://console.groq.com/docs/rate-limits

---

## 2. TTS narration (Amharic first; also Afaan Oromo, Tigrinya, Somali)

Language support, from each provider's docs:

| Provider / model | Amharic | Tigrinya | Somali | Afaan Oromo |
|---|---|---|---|---|
| Gemini API `gemini-3.8-flash-tts` [g-tts] | Yes | Yes | Yes | No |
| Gemini API `gemini-3.8-flash-lite-tts` [g-tts] | Yes | No | No | No |
| Google Cloud TTS, Gemini-TTS [gc-tts] | Preview | No | No | No |
| Azure Speech [az-lang] | Yes (2 voices) | No | Yes (2 voices) | No |
| ElevenLabs Eleven v4 / v4 Turbo [el-models] | Yes | No | Yes | No |
| ElevenLabs v3, Multilingual v2, Flash [el-models] | No | No | v3 only | No |
| OpenAI TTS [oa-tts] | No | No | No | No |
| Meta MMS-TTS (open weights) [mms-amh] [mms-orm] | Yes (needs uroman romanization) | not checked | not checked | Yes |

| Provider | Model | Price | Free tier / limits | Ethiopia / payment | Output licence | Notes |
|---|---|---|---|---|---|---|
| Gemini API | `gemini-3.8-flash-tts` | In $0.50 text, out $9.00 audio per 1M tokens (≈ $0.00225 per 10 s) until 2026-12-31, then $1.00 / $18.00 [g-price] | Free of charge [g-price] | Ethiopia listed [g-regions] | Google won't claim ownership [g-terms] | 24 kHz mono WAV. 30 prebuilt voices. Auto language detection [g-tts] |
| Gemini API | `gemini-3.8-flash-lite-tts` | In $0.50, out $6.00 per 1M (≈ $0.0015 per 10 s) [g-price] | Free of charge [g-price] | same | same | Amharic yes, no Tigrinya/Somali [g-tts] |
| Azure Speech | `am-ET-MekdesNeural` (F), `am-ET-AmehaNeural` (M); `so-SO-UbaxNeural`, `so-SO-MuuseNeural` [az-lang] | Dollar prices hidden on page [az-price] | F0: 0.5M characters free per month (neural) [az-price] | Not checked | Not checked | Good backup. Real voices, not generic |
| ElevenLabs | Eleven v4 | 1 credit per character via API [el-price]. v3 / Multilingual v2: $0.08 per 1K chars; Flash/Turbo $0.04 [el-api] | Free: 10K credits/month [el-price] | Not checked | Free plan has no commercial licence; Starter ($6/mo) adds it [el-price] | Only v4 has Amharic [el-models] |
| Google Cloud TTS | `gemini-2.5-flash-tts`, `gemini-3.1-flash-tts-preview` etc. | Not readable on page | Not readable | Not checked | | Amharic is Preview only. The 3.8 TTS models are not on Cloud TTS [gc-tts] |
| OpenAI | `gpt-4o-mini-tts`, `tts-1`, `tts-1-hd` | Not stated on guide | | Ethiopia supported [oa-countries] | | No Amharic. All three shut down 2027-01-06 [oa-tts] |
| Alibaba Model Studio | `qwen3-tts-flash` | $0.10 per 10K chars (Singapore) [ali-price] | 10K chars free [ali-price] | Not checked | | Amharic support not checked |
| OpenRouter | `google/gemini-3.8-flash-lite-tts`, `elevenlabs/eleven-v3`, others [or-tts] | Per character; rates not on guide page [or-tts] | `heygen/heygen-voice-1-turbo:free` exists [or-tts] | Takes USDC [or-faq] | | OpenAI-compatible `/api/v1/audio/speech` |
| Meta MMS-TTS | `facebook/mms-tts-amh`, `facebook/mms-tts-orm` | — | Not deployed by any Inference Provider [mms-amh] [mms-orm] | — | **CC-BY-NC 4.0, non-commercial** [mms-amh] | Self-host only. Only real option for Afaan Oromo, but non-commercial |

**Voice cloning consent.** Gemini voice replication needs a recorded consent statement from the same adult speaker and a paid Tier 1+ project [g-clone]. ElevenLabs bans cloning a living person's voice "without their explicit and informed consent" [el-policy]. OpenAI requires you to tell listeners the voice is AI-generated [oa-tts].

**Judgement.** Gemini 3.8 Flash TTS is the clear pick: free, Amharic, Tigrinya and Somali, one key shared with the LLM. Azure F0 is the backup for Amharic and Somali. No hosted service I checked supports Afaan Oromo; the only option is self-hosting MMS-TTS, and its licence is non-commercial.

[g-tts]: https://aistudio.google.com/docs/speech-generation
[g-clone]: https://aistudio.google.com/docs/voice-replication
[gc-tts]: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
[az-lang]: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
[az-price]: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/
[el-models]: https://elevenlabs.io/docs/overview/models
[el-api]: https://elevenlabs.io/pricing/api
[el-price]: https://elevenlabs.io/pricing
[el-policy]: https://elevenlabs.io/use-policy
[oa-tts]: https://developers.openai.com/api/docs/guides/text-to-speech
[oa-countries]: https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories
[ali-price]: https://www.alibabacloud.com/help/en/model-studio/model-pricing
[or-tts]: https://openrouter.ai/docs/guides/overview/multimodal/tts
[mms-amh]: https://huggingface.co/facebook/mms-tts-amh
[mms-orm]: https://huggingface.co/facebook/mms-tts-orm

---

## 3. Keyframe images with reference images (character consistency)

| Provider | Model | Price | Free tier / limits | Ethiopia / payment | Output / model licence | Notes |
|---|---|---|---|---|---|---|
| Cloudflare Workers AI | `@cf/black-forest-labs/flux-2-klein-4b` | $0.000287 per 512×512 output tile, $0.000059 per input tile [cf-price] | 10,000 neurons/day free on Free and Paid plans; then $0.011 per 1K neurons (Paid only) [cf-price]. Text-to-image: 720 req/min [cf-limits] | Free plan: no card needed per Cloudflare's product page (seen in search, not confirmed on fetch). Buying AI Gateway credits needs a non-prepaid card (seen in search) | Weights Apache 2.0 [hf-klein4] | Up to 4 reference images as `input_image_0..3`, each under 512×512. Output 256–1920 px [cf-klein]. ≈ $0.0014 (≈ 127 neurons) per 1024×768 image with 4 refs, so ≈ 75 images/day free (my math) |
| Cloudflare Workers AI | `@cf/black-forest-labs/flux-2-klein-9b` | $0.015 first MP, $0.002 next MP, $0.002 per input MP [cf-price] | in the 10K neurons | same | Weights: FLUX Non-Commercial [hf-klein9] | ≈ 1,364 neurons per 1 MP image: only ≈ 7 free/day [cf-price] |
| Cloudflare Workers AI | `@cf/black-forest-labs/flux-1-schnell` | $0.0000528 per tile + $0.0001056 per step [cf-price] | in the 10K neurons | same | | No reference images [cf-models] |
| Black Forest Labs API | FLUX.2 [klein] 4B | $0.014 first MP, $0.001 next MP, $0.001/MP per reference [bfl-price] | Not stated | Not checked | | FLUX 3 Image Klein $0.009 per 1K image [bfl-price] |
| Black Forest Labs API | FLUX.2 [pro] | $0.03 first MP, $0.015 next/ref MP [bfl-price] | | | | |
| fal | FLUX 2 Flash / FLUX 2 (edit) | $0.005/MP / $0.012/MP [fal-price] | No free API credits stated [fal-billing] | Prepaid credits; methods not stated [fal-billing] | | Nano Banana $0.0398, Nano Banana 2 $0.08, Seedream 4.5 $0.04 per image [fal-price] |
| Gemini API | `gemini-nano-banana-2.1` | ≈ $0.0336 per 1K image [g-price] | **Not available on free tier** [g-price] | Ethiopia listed; paid needs billing [g-billing] | Google won't claim ownership [g-terms] | `gemini-3.1-flash-image` ≈ $0.067 per 1K image [g-price] |
| OpenRouter | `black-forest-labs/flux.2-klein-4b` (0–4 refs), `google/gemini-nano-banana-2.1` (0–14 refs), many more [or-imgmodels] | Not readable from API | `recraft/recraft-v4.1-flash-v2:free` (text only, no refs) [or-imgmodels] | USDC accepted [or-faq] | | `POST /api/v1/images`, refs via `input_references` [or-img] |
| Together AI | FLUX.2 [dev] $0.0154/img; Qwen Image $0.0058/img; Nano Banana $0.039/img [tg-price] | | No free credits stated [tg-price] | Not checked | | |
| Replicate | FLUX schnell ≈ $0.003/img; FLUX dev $0.025/img [rep-price] | | Some models free for a while, then billing [rep-billing] | Not checked | | No klein price on pricing page |
| Alibaba Model Studio | `qwen-image-2.1-turbo` $0.016/img; `wan2.7-image` $0.03/img [ali-price] | | 10 and 50 free images [ali-price] | Account info must be completed [ali-free] | | Singapore region only for free quota [ali-free] |

**Judgement.** Cloudflare FLUX.2 klein 4B is free for this volume (30 images ≈ 3,800 neurons, under the 10K daily quota) and takes 4 reference images. The 512×512 cap on reference images is a real limit for face detail, so test it. BFL's own klein 4B API is the paid backup at about $0.015 per image.

[cf-price]: https://developers.cloudflare.com/workers-ai/platform/pricing/
[cf-limits]: https://developers.cloudflare.com/workers-ai/platform/limits/
[cf-models]: https://developers.cloudflare.com/workers-ai/models/
[cf-klein]: https://developers.cloudflare.com/changelog/post/2026-01-15-flux-2-klein-4b-workers-ai/
[hf-klein4]: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
[hf-klein9]: https://huggingface.co/black-forest-labs/FLUX.2-klein-9B
[bfl-price]: https://bfl.ai/pricing
[fal-price]: https://fal.ai/pricing
[fal-billing]: https://fal.ai/docs/documentation/model-apis/pricing
[or-img]: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
[or-imgmodels]: https://openrouter.ai/api/v1/images/models
[tg-price]: https://www.together.ai/pricing
[rep-price]: https://replicate.com/pricing
[rep-billing]: https://replicate.com/docs/topics/billing
[ali-free]: https://www.alibabacloud.com/help/en/model-studio/new-free-quota

---

## 4. Image-to-video

"Per 5 s" is my math from the per-second rate unless the page gave a per-clip price.

| Provider | Model | 480p | 720p | Free tier | Ethiopia / payment | Licence | Notes |
|---|---|---|---|---|---|---|---|
| WaveSpeed | Wan 2.2 I2V Ultra Fast | $0.05 per 5 s [ws-480] | $0.10 per 5 s [ws-720] | $1 free for eligible new accounts, no card [ws-price] | Cards, PayPal, Google Pay, Apple Pay, Alipay, WeChat Pay; "availability varies by region" [ws-price] | Wan 2.2: Apache 2.0, no rights claimed on outputs [hf-wan] | 5 or 8 s only [ws-480] |
| Alibaba Model Studio | `wan2.2-i2v-flash` (silent) | $0.015/s → $0.075 | $0.036/s → $0.18 | No free quota for this model [ali-price] | Account info must be completed [ali-free] | Apache 2.0 [hf-wan] | Singapore region. `wan3.0-video` has 30 s free [ali-price] |
| Alibaba Model Studio | `wan2.6-i2v-flash` (silent) | — | $0.025/s → $0.125 [ali-price] | none | | | |
| fal | Grok Imagine Video 1.5 Lite | $0.02/s → $0.10 | $0.03/s → $0.15 | + $0.01 per input image [fal-grok] | Prepaid; methods not stated [fal-billing] | | Also on OpenRouter, 1–15 s, 480p/720p/1080p [or-grok] |
| fal | MiniMax H3 Max Turbo | $0.025/s → $0.125 | 768p: $0.04/s → $0.20 | Promo ended 2026-11-15 [fal-h3] | | | |
| fal | PixVerse V6 | 360p $0.025/s; 540p $0.035/s | $0.045/s → $0.225 (no audio) [fal-pix] | | | | |
| fal | Wan 2.2 A14B | $0.04/s → $0.20 | $0.08/s → $0.40 [fal-wan14] | | | Apache 2.0 | Billed at 16 fps; default 81 frames ≈ 5 s |
| fal | Wan 2.2 TI2V-5B | — | $0.15 per video (580p/720p) [fal-wan5] | | | "Commercial use" label [fal-wan5] | **Removed on 2027-01-04** [fal-wan5] |
| fal | Wan 3.0 | $0.05/s → $0.25 | $0.10/s → $0.50 [fal-wan3] | | | | |
| OpenRouter | `x-ai/grok-imagine-video-1.5-lite` | 2 ¢/s | 3 ¢/s [or-video] | — | USDC accepted [or-faq] | | Same model as fal row, one key |
| OpenRouter | `google/veo-3.1-lite` | — | Listed 0.03 (no audio) / 0.05 (audio) per s in API; model page says "from $0.05/second" [or-video] [or-veo] | — | | | 4, 6 or 8 s only [or-veo] |
| OpenRouter | `alibaba/wan-3.0`, `minimax/hailuo-3-max` | $0.05/s each | $0.10/s; Hailuo 768p $0.08/s [or-video] | | | | |
| Gemini API | `gemini-omni-1.2-flash` | — | ≈ $0.07/s [g-price] | **Not available on free tier** [g-price] | Ethiopia listed | | Veo not on Gemini API price page |
| Runway API | `gen4_turbo` | 5 credits/s × $0.01 = $0.05/s → $0.25 [rw-price] | (resolution not stated) | | | | `gen4.5`: 12 credits/s [rw-price] |
| MiniMax API | MiniMax-Hailuo-02 | 512p 6 s: $0.10 | 768p 6 s: $0.28 [mm-price] | | | | Listed as legacy models |
| Kling API | Kling 2.5 Turbo / 3.0 / 4.0 | | See Could not verify | | | | Seen in search: smallest package $500 |
| Luma API | Ray 3.2 | 540p 5 s: 50 credits | 720p 5 s: 100 credits [luma-api] | | | | No dollar rate on page |
| Hugging Face Inference Providers | HunyuanVideo 1.5 via fal [hf-hy] | | | No free credits for free users [hf-ip] | | Tencent licence, **not valid in EU, UK, South Korea**; no rights claimed on outputs [hf-hy-lic] | fal price page for it returned 404 |

**Judgement.** WaveSpeed Wan 2.2 Ultra Fast is the cheapest I could verify: $0.10 per 5 s at 720p, $0.05 at 480p, and the $1 sign-up credit covers a test film at 480p. Alibaba `wan2.2-i2v-flash` is a close second at 480p. Grok Imagine 1.5 Lite through OpenRouter is the best "one key, pay with crypto" backup at $0.15 per 5 s at 720p. Quality and character consistency differ a lot between these models, so run one test shot on each before committing.

[ws-480]: https://wavespeed.ai/docs/docs-api/wavespeed-ai/wan-2.2-i2v-480p-ultra-fast
[ws-720]: https://wavespeed.ai/docs/docs-api/wavespeed-ai/wan-2.2-i2v-720p-ultra-fast
[ws-price]: https://wavespeed.ai/pricing
[hf-wan]: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
[fal-grok]: https://fal.ai/models/xai/grok-imagine-video/v1.5/lite/image-to-video
[fal-h3]: https://fal.ai/models/minimax/h3-max-turbo/image-to-video
[fal-pix]: https://fal.ai/models/fal-ai/pixverse/v6/image-to-video
[fal-wan14]: https://fal.ai/models/fal-ai/wan/v2.2-a14b/image-to-video/llms.txt
[fal-wan5]: https://fal.ai/models/fal-ai/wan/v2.2-5b/image-to-video
[fal-wan3]: https://fal.ai/models/alibaba/wan-3.0/image-to-video
[or-video]: https://openrouter.ai/api/v1/videos/models
[or-grok]: https://openrouter.ai/x-ai/grok-imagine-video-1.5-lite
[or-veo]: https://openrouter.ai/google/veo-3.1-lite
[rw-price]: https://docs.dev.runwayml.com/guides/pricing/
[mm-price]: https://platform.minimax.io/docs/pricing/overview
[luma-api]: https://lumalabs.ai/api
[hf-hy]: https://huggingface.co/tencent/HunyuanVideo-1.5
[hf-hy-lic]: https://huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE
[hf-ip]: https://huggingface.co/docs/inference-providers/pricing

---

## 5. Music (instrumental score, optional songs with lyrics)

| Provider | Model | Price | Free tier | Ethiopia / payment | Output licence | Notes |
|---|---|---|---|---|---|---|
| WaveSpeed | ACE-Step 1.5 | $0.0003/s → 90 s ≈ $0.027 [ws-ace] | $1 sign-up credit [ws-price] | see section 4 | Model MIT; output use not addressed; asks you to disclose AI use [ace-gh] | 5–240 s. No lyrics = instrumental [ws-ace] |
| fal | ACE-Step (version not stated) | $0.0002/s → 90 s ≈ $0.018 [fal-ace] | none stated | prepaid | "Commercial use" label [fal-ace] | Default 60 s. `[instrumental]` tag for no vocals |
| Stability AI | Stable Audio 2.5 / 3.0 | 8 credits = $0.08 per generation [stab-price] | 25 free credits (≈ 3 tracks) [stab-price] | Not checked | Not stated on pricing page | |
| Gemini API | `lyria-3.5` (full song) | $0.08 per song [g-price] | **Not available on free tier** [g-price] | Ethiopia listed | Google won't claim ownership [g-terms] | SynthID watermark. Vocals, lyrics or instrumental. Blocks artist-voice prompts [g-music] |
| Gemini API | `lyria-3-clip-preview` | $0.04 per 30 s clip [g-price] | not free | | | Always 30 s [g-music] |
| ElevenLabs | Eleven Music v2.5 | $0.15/min API [el-api] | Music API is for paid subscribers [el-music] | Not checked | Commercial use from Starter ($6/mo) [el-price] | 3 s – 5 min [el-music] |
| fal | Lyria 3 Pro / MiniMax Music v2 | $0.08 per audio / $0.03 per generation [fal-price] | | | | |
| MiniMax API | Music-2.x | $0.03–$0.15 per track [mm-price] | | | | **Closed to new users since 2026-08-20** [mm-price] |
| Alibaba Model Studio | `fun-music-v1` | $0.000275/s [ali-price] | none | | | China (Beijing) region only |
| Mubert API | — | Not on page [mubert] | | | Page says "royalty-free" [mubert] | Pricing not verified |
| OpenRouter | — | No music endpoint in docs [or-multi] | | | | |

**Judgement.** ACE-Step 1.5 on WaveSpeed or fal is almost free (3 × 90 s under $0.10) and the model is MIT. That keeps music on the same account as video if you use WaveSpeed. Stable Audio (25 free credits) or Lyria 3.5 ($0.08 per song) are good backups if ACE-Step quality is not enough.

[ws-ace]: https://wavespeed.ai/models/wavespeed-ai/ace-step-1.5
[ace-gh]: https://github.com/ace-step/ACE-Step-1.5
[fal-ace]: https://fal.ai/models/fal-ai/ace-step
[stab-price]: https://docs.stability.ai/pricing
[g-music]: https://aistudio.google.com/docs/music-generation
[el-music]: https://elevenlabs.io/docs/capabilities/music
[mubert]: https://mubert.com/api
[or-multi]: https://openrouter.ai/docs/guides/overview/multimodal/overview

---

## 6. Hugging Face: Inference Providers and ZeroGPU Spaces

| Item | What you get | Source |
|---|---|---|
| Inference Providers, free account | **No monthly credits.** You must buy credits to use it. | [hf-ip] |
| Inference Providers, PRO ($9/mo) | $2/month credits, usable on all HF compute | [hf-ip] [hf-pricing] |
| Inference Providers pricing | Provider's price, no HF markup. Routing is now powered by OpenRouter | [hf-ip] [hf-ipindex] |
| ZeroGPU, unauthenticated | 2 min GPU/day, low priority | [hf-zgpu] |
| ZeroGPU, free account | 5 min GPU/day, medium priority. Can host 2 ZeroGPU Spaces if account is 30+ days old | [hf-zgpu] |
| ZeroGPU, PRO | 40 min/day, extra at $1 per 10 min | [hf-zgpu] |
| ZeroGPU hardware | Half an RTX Pro 6000 Blackwell (48 GB), or full (96 GB) at 2× quota | [hf-zgpu] |

**Judgement.** This is no longer a free middle ground. Free users get no Inference credits, and 5 minutes of ZeroGPU a day is about one or two video clips. It is useful only for trying a model in a Space before paying elsewhere.

[hf-pricing]: https://huggingface.co/pricing
[hf-ipindex]: https://huggingface.co/docs/inference-providers/index
[hf-zgpu]: https://huggingface.co/docs/hub/spaces-zerogpu

---

## 7. Fallback: self-host on Kaggle or Colab (last resort)

| Platform | Free GPU | Limits | Source |
|---|---|---|---|
| Kaggle | Base quota about 30 GPU hours/week; T4 is the only GPU left after P100 was retired 2026-09-15 (user report) | Sessions up to 9 h (tips page, seen in search) | See Could not verify |
| Colab | GPU type varies over time | Not guaranteed; limits not published and "sometimes fluctuate"; max 12 h per session | [colab-faq] |

Model needs for self-hosting: Wan 2.2 TI2V-5B needs about 24 GB VRAM (e.g. RTX 4090) with offloading [hf-wan]. HunyuanVideo 1.5 needs 14 GB with offloading [hf-hy]. A single free T4 has 16 GB, so Wan 5B likely won't fit (my inference, not tested).

**Judgement.** Do not build the main pipeline on this. Notebooks break the "clone, set keys, run one command" goal and free GPU time is not guaranteed.

[colab-faq]: https://research.google.com/colaboratory/faq.html

---

## OpenRouter: what it covers now

- **Images:** yes, `POST /api/v1/images`, 71 models incl. FLUX.2 klein 4B and Nano Banana 2.1, reference images via `input_references` [or-img] [or-imgmodels].
- **Video:** yes, async `POST /api/v1/videos`, 30 models incl. Grok Imagine 1.5 Lite, Wan 3.0, Veo 3.1 Lite/Fast, Hailuo 3, Seedance 2.x [or-video]. No Sora in the current list.
- **TTS:** yes, `POST /api/v1/audio/speech` (OpenAI-compatible), incl. Gemini 3.8 Flash-Lite TTS and Eleven v3 [or-tts].
- **Music:** no endpoint in the docs [or-multi].

So OpenRouter can cover four of the five stages with one key and USDC payment. That matters for users without an international card.

---

## Could not verify

Things I could not confirm from a primary source on 2026-11-25. Do not budget on these without checking.

- **Gemini free-tier rate limits** (RPM/RPD) for 3.8 Flash and 3.8 Flash TTS. Docs say to look in AI Studio [g-rate]. A free key may run out mid-film.
- **Amharic text quality** of any LLM. No provider states it.
- **Country support for Ethiopia** at Cloudflare, fal, WaveSpeed, Replicate, Alibaba Cloud, ElevenLabs, Azure, Stability, Groq, BFL, Together, Hugging Face. Only Gemini [g-regions] and OpenAI [oa-countries] were confirmed.
- **Cloudflare Free plan needs no card.** Seen only in a search snippet of cloudflare.com/products/workers-ai; the fetched page did not say it.
- **Cloudflare tile rounding** for 1024×768 output (I assumed 4 tiles).
- **fal payment methods and free credits.** fal docs only say "prepaid credits" [fal-billing]. A fal learn page (search snippet) said new accounts start at zero.
- **HunyuanVideo 1.5 price on fal.** The model page returned 404. A search snippet said $0.075/s.
- **Replicate prices** for Wan 2.2 i2v fast, ACE-Step and FLUX klein. Model pages did not render prices. Old launch blog said $0.05 per 480p video; ACE-Step pages showed run estimates of ≈ $0.02–$0.13.
- **Kling API prices.** The price page did not render. A search snippet of Kling's docs showed a $500 minimum package and 0.3 units/s for Kling 2.5 Turbo at 720p.
- **Luma API dollar price.** Page gives credits only, and its FAQ figures (0.15 / 0.30) do not match its table.
- **Together AI video prices.** Page lists them "per video" (e.g. Veo 3.1 $0.08), which looks like per-second. Unclear.
- **Veo 3.1 Lite on OpenRouter.** API says 3 ¢/s at 720p without audio; model page says "from $0.05/second".
- **Google Cloud TTS and Azure Speech dollar prices.** Pages did not show them.
- **ElevenLabs Eleven v4 dollar price per 1K characters.** Only "1 credit per character" is stated.
- **Stable Audio output licence and max length.** Not on the pricing page.
- **Mubert API pricing and licence.** Not on the page.
- **OpenRouter current free text models and image/TTS prices.** The listing pages did not return them.
- **Groq free plan limits.** Only shown in the logged-in console.
- **Kaggle GPU quota.** Kaggle pages did not render; the 30 h/week and 9 h session figures come from search snippets of kaggle.com pages. The P100 retirement is a user forum post.
- **ACE-Step version on fal.** fal does not say if it is 1.5.
- **Tigrinya and Somali in MMS-TTS.** Not checked.
