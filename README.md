# NarrateAnimateAwesomeGreat

**Your story + your narrated voice + key images → a synchronized, animated, YouTube-ready movie.**

NarrateAnimateAwesomeGreat (StoryForge) is a narration-first long-form illustrated-video pipeline. Your recording is the **master clock**. Story text supplies semantic structure, keyframes establish visual identity, generated clips add motion where it matters, and FFmpeg deterministically assembles the film.

The project is structured as a VS Code multi-agent workspace:

- **Codex** reads `AGENTS.md` and acts as builder/integrator.
- **Claude** reads `CLAUDE.md` and acts as adversarial production/code reviewer.
- **StoryForge MCP** gives both agents the same controlled project tools.
- **Google Flow/Veo subscription generation is the preferred cloud path.**
- **Local GPU generation/animation is preferred before separately billed APIs.**
- **Paid Gemini/Runway API calls are disabled by default.**
- **Your local NVIDIA GPU** handles local I2V experiments, deterministic rendering and optional enhancement/upscaling.

The goal is not to pay a video model to generate every second. The goal is to exhaust already-paid subscription and local options first, then use billable API generation only when explicitly enabled.

## Architecture

```text
                    VS CODE
        +-----------------------------+
        | Codex          Claude       |
        | builder        reviewer     |
        +-------------+---------------+
                      |
                 StoryForge MCP
                      |
 story.txt + narration.wav + keyframes/
                      |
                      v
              narration alignment
                      |
              work/manifest.json
                      |
                Director / Router
      +---------------+----------------+
      |               |                |
 STILL_MOTION     LOCAL_VIDEO    FLOW_SUBSCRIPTION
      |               |                |
      +---------------+----------------+
                      |
          paid API only if enabled
                      |
                    FFmpeg
             narration + SFX/music
                      |
             youtube_master.mp4
                      |
              optional local upscale
```

## Default generation waterfall

StoryForge now routes scenes in this order:

```text
1. EXISTING_VIDEO      already generated/imported                 $0 incremental
2. STILL_MOTION        FFmpeg pan/zoom/crop from keyframe         $0
3. LOCAL_VIDEO         local Wan/ComfyUI/other 8 GB-safe path     $0 API
4. FLOW_SUBSCRIPTION   manual Google Flow/Veo generation          $0 incremental accounting
5. CHEAP_CLOUD         separately billed API                      disabled by default
6. HERO_CLOUD          premium separately billed API              disabled by default
```

`FLOW_SUBSCRIPTION` means StoryForge creates a self-contained scene packet for Google Flow. It does **not** automate or scrape the consumer Flow UI and does not require a Gemini API key.

## Features

- narration controls all scene timing
- optional faster-whisper alignment
- automatic SRT subtitles
- cinematic pan/zoom animation for still keyframes
- generated video automatically overrides a still scene
- production validation/inspection
- automatic scene routing: `STILL_MOTION`, `LOCAL_VIDEO`, `FLOW_SUBSCRIPTION`, `CHEAP_CLOUD`, `HERO_CLOUD`, `EXISTING_VIDEO`
- project generation-cost estimator
- configurable hard budget threshold
- Google Flow/Veo subscription packet exporter
- Google Veo API adapter retained as an explicit separately billed fallback
- isolated Runway adapter retained as an explicit separately billed fallback
- zero-API/manual generation mode
- provider-neutral generation interface
- NVIDIA/NVENC final encode when available
- optional Real-ESRGAN local upscale
- background music and per-scene SFX
- MCP server for Codex/Claude/IDE automation
- `.env` configuration with secrets excluded from Git

## Quick start — Windows

```powershell
git clone https://github.com/BradyLoreeVillianyLabs/NarrateAnimateAwesomeGreat.git
cd NarrateAnimateAwesomeGreat

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[whisper,mcp,dev]"

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
```

Build the timeline and Director plan:

```powershell
storyforge plan projects\my-story --whisper
storyforge validate projects\my-story
storyforge director projects\my-story
storyforge cost projects\my-story
storyforge prompts projects\my-story
```

The Director writes:

```text
projects/my-story/work/director_plan.json
```

Render immediately if desired:

```powershell
storyforge render projects\my-story
```

Scenes without generated video use local animated keyframes.

## Google Flow subscription workflow

Export only the scenes the Director believes need subscription/cloud motion:

```powershell
storyforge flow-pack projects\my-story
```

This creates:

```text
projects/my-story/work/flow_packets/
  INDEX.json
  scene_004/
    keyframe.png
    prompt.txt
    context.json
    OUTPUT_NAME.txt
  scene_009/
    ...
```

For each packet:

1. Open Google Flow.
2. Upload `keyframe.*` when present.
3. Use `prompt.txt`.
4. Start with the cheapest practical Flow/Veo tier.
5. Download the clip using the filename in `OUTPUT_NAME.txt`.
6. Copy it into the project's `generated/` folder.

Example:

```text
projects/my-story/generated/scene_004.mp4
```

Then:

```powershell
storyforge validate projects\my-story
storyforge render projects\my-story
```

StoryForge substitutes the new clip automatically while keeping narration timing unchanged.

## Paid API safeguard

Separately billed APIs are disabled by default even if keys exist:

```dotenv
STORYFORGE_ENABLE_PAID_API=0
```

Trying to run:

```bash
storyforge generate projects/my-story --provider veo
```

will fail closed while that setting is `0`.

Only if you deliberately want separately billed API generation should you set:

```dotenv
STORYFORGE_ENABLE_PAID_API=1
```

This separation prevents a Gemini API key from silently converting your already-paid Flow subscription workflow into pay-as-you-go API usage.

## VS Code agent workflow

Codex receives its standing instructions from `AGENTS.md`. Claude receives a deliberately different reviewer contract from `CLAUDE.md`.

Recommended loop:

```text
1. You add story + narration + keyframes.
2. Codex validates and builds the Director plan.
3. Claude reviews continuity, pacing, prompts and unnecessary spend.
4. Codex reproduces/verifies Claude findings and fixes justified issues.
5. StoryForge exports Flow packets for scenes that actually need motion.
6. You generate those scenes in Flow and/or locally.
7. Clips arrive as generated/scene_###.mp4.
8. StoryForge renders a preview/final.
9. Claude reviews remaining production weaknesses.
10. Final render + local upscale if useful.
```

See `docs/VS_CODE_AGENTS.md`.

## Provider/status checks

```bash
storyforge providers
```

The command reports capability/presence only. It never prints secret values.

Typical defaults:

```json
{
  "flow_subscription": true,
  "paid_api_enabled": false,
  "veo_api_key_present": false,
  "runway_key_present": false,
  "generic_key_present": false,
  "comfyui": true
}
```

## Budget configuration

`.env` contains planning rates and the project limit:

```dotenv
STORYFORGE_USE_FLOW_SUBSCRIPTION=1
STORYFORGE_ENABLE_PAID_API=0
STORYFORGE_MAX_PROJECT_GENERATION_USD=20.00
STORYFORGE_FLOW_INCREMENTAL_USD_PER_SECOND=0.00
STORYFORGE_LOCAL_VIDEO_USD_PER_SECOND=0.00
STORYFORGE_CHEAP_CLOUD_USD_PER_SECOND=0.05
STORYFORGE_HERO_CLOUD_USD_PER_SECOND=0.15
```

These values are accounting/configuration assumptions, not provider billing claims. StoryForge treats Flow/local routes as zero incremental API cost by default because you already pay for the subscription/hardware. Update the rates if you want electricity, subscription amortization, or current API pricing reflected in project estimates.

## MCP

Install and start:

```bash
pip install -e '.[mcp]'
storyforge-mcp
```

The project-scoped MCP façade exposes:

- provider status
- list/create project
- inspect/validate project
- plan narration timeline
- build Director plan
- estimate separately billed generation cost
- export provider-neutral prompts
- export Google Flow subscription packets
- dry-run or execute selected generation
- render validated project

MCP generation defaults to the Flow workflow and separately billed APIs remain blocked unless `.env` explicitly enables them.

See `docs/MCP.md` and `docs/VS_CODE_AGENTS.md`.

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
    director_plan.json
    subtitles.srt
    generation_queue.csv
    prompts/
    flow_packets/
    reviews/
  output/
    youtube_master.mp4
```

## Scene manifest

`work/manifest.json` is the canonical timeline:

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

The renderer does not care whether `scene_004.mp4` came from Flow, local Wan, ComfyUI, Veo API, Runway, or another future generator.

## Cost philosophy

For a 15-minute film, do **not** automatically generate 900 seconds of cloud video. A more economical production could contain roughly:

```text
250 sec Flow subscription motion
200 sec local generated animation
350 sec animated illustrations
100 sec titles/transitions/establishing beats
```

That can yield a 900-second finished movie with little or no incremental API spend.

## Development

```bash
pip install -e '.[dev]'
python -m compileall src
pytest -q
```

Agent behavior is governed by `AGENTS.md` and `CLAUDE.md`. Never commit `.env`, API credentials, private narration recordings, or paid/generated movie assets unless you intentionally want them in source control.
