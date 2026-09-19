---
name: kie-ai-multimedia-orchestrator
description: Orchestrates image, video, music, speech and multi-modal media generation through the Kie AI API (docs.kie.ai, kie.ai/market). Use this skill whenever the user wants to generate or edit images, create videos, compose music, produce text-to-speech or voiceovers, or build a multi-step media piece (trailer, music video, animated ad) with Kie AI models such as Seedream, Nano Banana, Flux, GPT Image, Kling, Seedance, Hailuo, Wan, Veo, Runway, Suno or ElevenLabs. Trigger on text-to-image, image-to-video, text-to-video, AI music, TTS, "generate with Kie", or any mention of docs.kie.ai or kie.ai, even if the user doesn't name a model.
---

# Kie AI Multimedia Orchestrator

Turn a media request into a correct, minimal set of Kie AI tasks: decompose the request, read the *current* docs, pick a model per modality, build payloads, run the async task lifecycle, and deliver the assets.

Kie's catalog and API change constantly, so this skill deliberately contains no endpoints, model IDs or payload schemas. The live docs are the only source of truth, which is why step 2 is not optional.

## Step 1 - Decompose the request

Identify the modalities needed and how they depend on each other:

- **Image**: generate, edit, upscale, remove background
- **Video**: text-to-video, image-to-video, extend, upscale, lip sync/avatar
- **Audio**: music, speech (TTS), sound effects, stem/vocal separation

Write a short plan before spending credits, e.g.:

```
1. image  (text-to-image)  -> keyframe.png
2. video  (image-to-video) needs keyframe.png -> clip.mp4
3. audio  (music)          independent -> track.mp3
4. merge  (ffmpeg, local)  clip.mp4 + track.mp3 -> final.mp4
```

Dependencies matter because image-to-video and edit models take the earlier output as an input, so step N cannot start until step N-1 has succeeded. Independent branches (music vs. video) can be submitted in parallel. Check the docs, but expect to combine audio and video locally with ffmpeg.

If the request is ambiguous in a way that changes cost or output (duration, aspect ratio, vocals vs. instrumental, reference images), ask briefly. Otherwise pick sensible defaults and state them.

## Step 2 - Discover everything from the live docs

Do not rely on memory or on this file for endpoints, model IDs, parameter names, response shapes or status values. Kie changes them often (models get new versions, whole model families move from a dedicated API to the unified Market API), and a wrong guess wastes credits. Discover them each time:

1. Fetch `https://docs.kie.ai/llms.txt` (the docs index). It lists every model family and API page, grouped by image / video / music-audio / common. Use `https://docs.kie.ai/` and `https://kie.ai/market` for overviews, pricing and tiers.
2. Open the page for the model you intend to use, and read from it: the create-task endpoint and method, the exact model ID, every input field with allowed values and limits (durations, aspect ratios, resolutions, whether a callback URL is required), the endpoint and response fields for checking status, and how results are returned.
3. Read the general pages for the account-level facts: base URL, authentication, the async task model, rate limits, webhook verification, file-upload and credits endpoints. Look for them in the index rather than assuming them.
4. Note any deprecation, "old version", or degraded/offline banner on the page; it feeds the fallback logic.

Model families change, so search the index for what is there now. The user's request usually names a family (Seedream, Nano Banana, Flux, GPT Image, Ideogram, Kling, Seedance, Hailuo, Wan, Veo, Runway, Suno, ElevenLabs...). If it doesn't, browse the index for the modality and read the candidates' pages.

If you cannot browse, say so plainly, and produce only a plan plus clearly-labelled placeholders (`<endpoint from docs>`), never invented paths or fields.

The docs are not always self-consistent (an endpoint page can name a different host than the quickstart, or two sections can give different retention periods). When a documented call fails or two pages disagree, read the related overview/quickstart page, try the alternative the docs give, and tell the user about the discrepancy instead of stopping or silently guessing.

## Step 3 - Select a model per modality

Choose from what the docs list *today*, based on the user's actual constraint: readable text in an image, character consistency, motion control, cinematic realism, native audio, speed and cost, duration limits, resolution. Compare the candidates' pages rather than reputation. Explain the choice in 2-4 lines (model, why, runner-up).

Prefer a cheaper tier for drafts when the user hasn't asked for final quality, and say so. Video is usually the expensive step, so get the keyframe right first.

## Step 4 - Build payloads and prompts

Build each request exactly as that model's page specifies. Read the API key from the environment (`KIE_API_KEY`); never hardcode it or echo it back. If it is unset, still produce the requests and commands, and tell the user where the docs say to get a key rather than stalling.

Write prompts for the target model, not generically, using what its page recommends: descriptive scene-and-motion language for video, concrete visual detail plus quoted text for images with lettering, genre/mood/instrumentation for music with lyrics in the lyrics field where one exists. Show the final prompt to the user.

Check inputs against the request before spending: does the requested duration match the model's allowed values and the script length (a one-line narration is seconds, not 30s), is the aspect ratio supported, is a reference image URL publicly reachable.

**Uploading user files.** Models take URLs, so a local file (photo, audio, video, document, anything the user supplies) has to be uploaded to Kie first. Before uploading, tell the user in one or two lines: the file will be sent to Kie's temporary storage, the link is reachable by anyone who has it until it expires, and the docs describe automatic expiry only, with no delete endpoint (re-check the upload pages in case that has changed). Proceed once the user has clearly asked for the task that needs the file; if they seem unaware or the file looks sensitive (IDs, private documents, other people's images), ask first. Prefer a URL the user already hosts publicly over uploading. Record the `expiresAt`/retention information returned by the upload, delete any temporary local copies you made (such as base64 dumps), and mention what remains stored, including the generated outputs, in your final summary.

**Cost.** Docs and model pages usually don't publish prices. Read the account balance (the credits endpoint on the docs' common pages) before and after each generation and report the real cost, and use minimal durations/resolutions/tiers for tests and drafts.

`scripts/kie_client.py` is a generic helper that creates a task, polls it and downloads results. It has no built-in endpoints; you pass the ones you discovered (`--help`). Write the request JSON to a file and pass `--body-file` (inline `--body` breaks on Windows shells); invoke Python as `python3` on macOS/Linux or `python`/`py` on Windows. It makes its HTTP calls with `curl` so corporate TLS-inspecting proxies (whose CA lives in the OS trust store) work; don't work around certificate errors by disabling verification.

## Step 5 - Run the async lifecycle

Kie is asynchronous: a successful create call returns a task id, which means the task was created, not finished. Confirm the specifics on the docs, then:

1. Submit and record the task id immediately; show it to the user.
2. Get results by polling the status endpoint the docs give (choose an interval that fits the modality: seconds for images/audio, longer for video), or via a callback URL if the user has a public endpoint. Don't invent a callback URL.
3. Interpret status/state values and result fields as the docs define them (results may be nested as a JSON string that needs parsing).
4. Download assets promptly; generated URLs are typically temporary.
5. Respect the rate limits on the docs' rules page, back off on throttling errors, and set a polling timeout. On timeout, report the task id instead of resubmitting, which would spend credits twice.

## Step 6 - Fallbacks

Switch models when the docs mark the model degraded/deprecated or a task fails with a model-side error. Do not switch for user-input errors (bad params, content-policy rejection, insufficient credits): fix the input or tell the user.

Fall back to the runner-up you named in step 3, in the same modality. Re-read that model's page for parameter differences, retry once, and tell the user which model was used and why. If there is no equivalent (a modality with a single option), report the failure instead.

## Multimodal pipelines

Run in dependency order: **Image -> Video -> Audio -> merge**. Confirm each stage's output exists and looks right before feeding it to the next; a bad keyframe wastes a video generation. Pass the previous output to the next stage the way the next model's page says (usually a public URL: use the result URL directly, or the file-upload API from the docs index if the source is local).

Check the chosen video model's allowed durations. If one clip can't cover the requested length, plan several clips (extend, or several image-to-video clips) plus one music track, joined with ffmpeg:

```bash
ffmpeg -i clip.mp4 -i track.mp3 -map 0:v -map 1:a -c:v copy -shortest final.mp4
```

For a 10s trailer: keyframe(s) -> 1-2 clips -> ~10-15s music -> trim/fade audio to video length. Check ffmpeg exists; if not, give the command instead.

## Output to the user

End with:
- **Plan & model choices** (one line each, with rationale)
- **Task table**: stage, model, taskId, status
- **Assets**: save to a folder visible in Finder/Explorer such as `~/Downloads`, not `/tmp`; give the full paths (and URLs with the note that they expire)
- **Actual cost** in credits, and anything uploaded to Kie and when it expires
- **Fallbacks/issues** encountered, and approximate credit-relevant decisions (draft vs. final tier)
- If nothing was executed (no key / dry run), the exact payloads and commands ready to run

Ask before any run likely to consume significant credits (multiple video generations, 4K tiers), since credits are the user's money.
