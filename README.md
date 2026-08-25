# NarrateAnimateAwesomeGreat

**Your story + your narrated voice + key images → a synchronized, animated, YouTube-ready movie.**

NarrateAnimateAwesomeGreat (StoryForge) is a narration-first long-form illustrated-video pipeline. Your recording is the **master clock**. Story text supplies semantic structure, keyframes establish visual identity, generated clips add motion where it matters, and FFmpeg deterministically assembles the film.

The project is also structured as a **VS Code multi-agent workspace**:

- **Codex** reads `AGENTS.md` and acts as builder/integrator.
- **Claude** reads `CLAUDE.md` and acts as adversarial production/code reviewer.
- **StoryForge MCP** gives both agents the same controlled project tools.
- **Gemini/Veo, Runway, local Wan/ComfyUI, or manual subscription workflows** can supply selected motion clips.
- **Your local NVIDIA GPU** handles deterministic rendering and optional enhancement/upscaling.

The goal is not to pay a video model to generate every second. The goal is to spend generation credits only where motion materially improves the movie.

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
          +-----------+-----------+
          |           |           |
     STILL_MOTION  LOCAL_VIDEO  CLOUD_VIDEO
          |           |           |
          +-----------+-----------+
                      |
                    FFmpeg
             narration + SFX/music
                      |
             youtube_master.mp4
                      |
              optional local upscale
```

## Features

- narration controls all scene timing
- optional faster-whisper alignment
- automatic SRT subtitles
- cinematic pan/zoom animation for still keyframes
- generated video automatically overrides a still scene
- production validation/inspection
- automatic scene routing: `STILL_MOTION`, `LOCAL_VIDEO`, `CHEAP_CLOUD`, `HERO_CLOUD`, `EXISTING_VIDEO`
- project generation-cost estimator
- configurable hard budget threshold
- Google Veo provider adapter
- isolated Runway adapter
- zero-API/manual subscription workflow
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

Build the timeline:

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

It classifies each scene and estimates generation spend before anything billable happens.

Render at any point:

```powershell
storyforge render projects\my-story
```

Scenes without generated video use local animated keyframes.

## VS Code agent workflow

Codex receives its standing instructions from `AGENTS.md`. Claude receives a deliberately different reviewer contract from `CLAUDE.md`.

Recommended loop:

```text
1. You add story + narration + keyframes.
2. Codex validates and builds the Director plan.
3. Claude reviews continuity, pacing, prompts and unnecessary spend.
4. Codex reproduces/verifies Claude findings and fixes justified issues.
5. StoryForge exports generation packets.
6. You use subscription interfaces and/or explicitly approve API jobs.
7. Clips arrive as generated/scene_###.mp4.
8. StoryForge renders a preview/final.
9. Claude reviews remaining production weaknesses.
10. Final render + local upscale.
```

See `docs/VS_CODE_AGENTS.md`.

## Add AI-generated motion

Copy `.env.example` to `.env` and fill only providers you actually use.

Check configuration without exposing keys:

```bash
storyforge providers
```

Inspect the budget first:

```bash
storyforge cost projects/my-story
```

Preview selected API jobs without spending:

```bash
storyforge generate projects/my-story --provider veo --scenes 1,4,8 --dry-run
```

Or use your paid subscription UI manually:

```bash
storyforge generate projects/my-story --provider manual
```

Put downloaded/generated clips at:

```text
projects/my-story/generated/scene_001.mp4
```

Re-render and StoryForge substitutes them automatically.

## Budget configuration

`.env` contains planning rates and the project limit:

```dotenv
STORYFORGE_MAX_PROJECT_GENERATION_USD=20.00
STORYFORGE_CHEAP_CLOUD_USD_PER_SECOND=0.05
STORYFORGE_HERO_CLOUD_USD_PER_SECOND=0.15
STORYFORGE_LOCAL_VIDEO_USD_PER_SECOND=0.00
```

These are **configuration/estimate values**, not authoritative provider pricing. Update them when your actual provider/model rates change.

A consumer ChatGPT/Claude/Gemini subscription is not assumed to include API billing. Subscription-assisted/manual production remains a first-class workflow.

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
- estimate generation cost
- export generation prompts
- dry-run or execute selected scene generation
- render validated project

Generation defaults to **dry-run through MCP**. MCP accepts project names rather than arbitrary filesystem paths.

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

The renderer does not care which generator produced `scene_004.mp4`.

## Cost philosophy

For a 15-minute film, do **not** automatically generate 900 seconds of cloud video. A more economical production could contain roughly:

```text
250 sec generated motion
400 sec animated illustrations
150 sec cinematic holds/pans
100 sec titles/transitions/establishing beats
```

The Director exists to make that decision scene-by-scene rather than treating every second as an API call.

## Development

```bash
pip install -e '.[dev]'
python -m compileall src
pytest -q
```

Agent behavior is governed by `AGENTS.md` and `CLAUDE.md`. Never commit `.env`, API credentials, private narration recordings, or paid/generated movie assets unless you intentionally want them in source control.
