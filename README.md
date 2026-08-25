# NarrateAnimateAwesomeGreat

**Your story + your narrated voice + a handful of key images → a synchronized, animated, YouTube-ready movie.**

NarrateAnimateAwesomeGreat (StoryForge CLI) is a narration-first production pipeline for long-form illustrated stories. Your voice recording is the **master clock**. Story text supplies semantic structure, keyframes establish the visual identity, generated clips add motion where it matters, and FFmpeg deterministically assembles the finished film.

The goal is not to pay a video model to generate every second. The goal is to spend generation credits where motion improves the story and let local rendering handle the rest.

## Pipeline

```text
story.txt + narration.wav + keyframes/
                  |
                  v
          narration alignment
                  |
                  v
        work/manifest.json
          /       |       \
         /        |        \
 local keyframe  I2V      captions
   animation    clips       / SFX
         \        |        /
          \       |       /
             FFmpeg
                |
                v
       youtube_master.mp4
                |
                v
       optional local upscale
```

## Features

- narration controls all scene timing
- optional faster-whisper alignment
- automatic SRT subtitles
- cinematic pan/zoom animation for still keyframes
- generated video automatically overrides a still scene
- Google Veo provider adapter
- isolated Runway adapter
- zero-API/manual generation mode
- provider-neutral generation interface
- NVIDIA/NVENC final encode when available
- optional Real-ESRGAN local upscale
- background music and per-scene SFX
- MCP server for agent/IDE automation
- `.env` configuration with secrets excluded from Git

## Quick start — Windows

```powershell
git clone https://github.com/BradyLoreeVillianyLabs/NarrateAnimateAwesomeGreat.git
cd NarrateAnimateAwesomeGreat

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[whisper,mcp]"

copy .env.example .env
storyforge doctor
storyforge init projects\my-story
```

Add:

```text
projects/my-story/story.txt
projects/my-story/narration.wav
projects/my-story/keyframes/001.png
projects/my-story/keyframes/002.png
...
```

Plan and render:

```powershell
storyforge plan projects\my-story --whisper
storyforge prompts projects\my-story
storyforge render projects\my-story
```

You already have a complete movie at this point. Scenes without generated video use animated keyframes.

## Add AI-generated motion

Copy `.env.example` to `.env` and fill only the provider you want.

Check configuration without exposing keys:

```bash
storyforge providers
```

Preview a generation batch without spending anything:

```bash
storyforge generate projects/my-story --provider veo --scenes 1,4,8 --dry-run
```

Then generate:

```bash
storyforge generate projects/my-story --provider veo --scenes 1,4,8
```

Or use a subscription/UI manually:

```bash
storyforge generate projects/my-story --provider manual
```

Put each downloaded clip at:

```text
projects/my-story/generated/scene_001.mp4
```

Run `storyforge render` again. StoryForge substitutes it automatically.

## API configuration

See `.env.example` and `docs/PROVIDERS.md`.

Optional installs:

```bash
pip install -e '.[veo]'
pip install -e '.[runway]'
pip install -e '.[mcp]'
pip install -e '.[all]'
```

**Never commit `.env`.** The repository ignores it. Provider status reports only whether credentials are present, never their values.

A paid consumer AI subscription and API billing are not necessarily the same product. Verify current API quota/pricing before launching large generation batches.

## MCP

Install:

```bash
pip install -e '.[mcp]'
```

Start:

```bash
storyforge-mcp
```

The MCP façade exposes:

- provider status
- list/create project
- plan project
- export generation prompts
- dry-run or execute selected scene generation
- render project

Generation defaults to **dry-run through MCP** to avoid an agent accidentally burning video credits.

See `docs/MCP.md` for host configuration and security notes.

## Project layout

```text
projects/my-story/
  story.txt
  narration.wav
  keyframes/
    001.png
    002.png
  generated/
    scene_001.mp4
  music/
    bed.mp3
  sfx/
    003_door.wav
  work/
    manifest.json
    subtitles.srt
    generation_queue.csv
    prompts/
  output/
    youtube_master.mp4
```

## Scene manifest

`work/manifest.json` is the canonical timeline. A scene resembles:

```json
{
  "id": 4,
  "start": 24.2,
  "end": 31.0,
  "duration": 6.8,
  "text": "Milo opened the tiny door.",
  "keyframe": "keyframes/002.png",
  "generated_video": "generated/scene_004.mp4",
  "motion": "push_in",
  "importance": 0.7
}
```

The renderer does not care which generator produced `scene_004.mp4`.

## Cost philosophy

For a 15-minute film, do **not** automatically generate 900 seconds of cloud video. A better first target might be:

```text
250 sec generated motion
400 sec animated illustrations
150 sec slow cinematic holds/pans
100 sec titles/transitions/establishing beats
```

That is how this architecture attacks generation cost.

## GTX 5060 8 GB role

Use the local GPU primarily for the jobs it can do reliably:

- NVENC encoding
- tiled Real-ESRGAN enhancement
- frame interpolation when genuinely useful
- small/quantized local video experiments
- ComfyUI/Wan experiments

Do not make a large local diffusion model a hard dependency for finishing a movie.

## Local upscale

When `realesrgan-ncnn-vulkan` is installed and on PATH:

```bash
storyforge upscale projects/my-story --scale 2
```

Upscale only after rejecting broken generations. Upscaling can improve linework and texture; it cannot repair wrong faces, extra limbs or continuity mistakes.

## Provider architecture

Every generator implements the small contract in `src/storyforge/providers/base.py`. Cloud APIs are adapters, not the foundation of the application.

That means Gemini/Veo, Runway, ComfyUI/Wan and future providers can all produce the same scene asset without rewriting the movie pipeline.

## Development

```bash
pip install -e '.[dev]'
pytest
```

Core rule: **the narration is the master clock and `manifest.json` is the canonical timeline.**

## Documentation

- `docs/PROVIDERS.md` — APIs, manual mode and provider adapters
- `docs/MCP.md` — MCP setup and security
- `.env.example` — all supported environment variables

## License

MIT. Third-party model weights, SDKs and generated assets retain their own licenses/terms.
