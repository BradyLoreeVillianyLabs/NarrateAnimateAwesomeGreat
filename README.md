# NarrateAnimateAwesomeGreat / StoryForge

**Story text + your narrated voice + guide images → storyboard/timeline → selective animation → synchronized YouTube-ready video.**

StoryForge is a narration-first production system for long-form illustrated stories. The narration is the **master clock**. Story text supplies semantic structure, guide images anchor visual continuity, generated clips add motion where it matters, and FFmpeg deterministically assembles the finished movie.

The project is designed around the tools already available on a development workstation:

- **Codex** — builder/integrator via `AGENTS.md`
- **Claude** — adversarial reviewer via `CLAUDE.md`
- **StoryForge Studio** — local graphical storyboard/timeline
- **StoryForge MCP** — controlled tool surface for IDE agents
- **Google Flow/Veo subscription** — preferred cloud video-generation path
- **local Wan/ComfyUI** — free/local I2V experiments when practical
- **FFmpeg/NVENC + Real-ESRGAN** — deterministic finishing on an NVIDIA GPU
- **separately billed APIs** — disabled by default

## Production architecture

```text
                    VS CODE
          Codex builder + Claude reviewer
                       |
                 StoryForge MCP
                       |
 story.txt + narration.wav + keyframes/
                       |
                 planner/alignment
                       |
               work/manifest.json
                       |
             +---------+---------+
             | StoryForge Studio |
             | timeline/filmstrip|
             +---------+---------+
                       |
                Director / Router
      +----------------+----------------+
      |                |                |
 STILL_MOTION     LOCAL_VIDEO    FLOW_SUBSCRIPTION
      |                |                |
      +----------------+----------------+
                       |
          paid API only if enabled
                       |
        FFmpeg + narration + music/SFX
                       |
              youtube_master.mp4
```

## Default generation waterfall

StoryForge tries to minimize incremental spend:

```text
1. EXISTING_VIDEO      imported/generated scene clip             $0
2. STILL_MOTION        FFmpeg pan/zoom from guide image          $0
3. LOCAL_VIDEO         local Wan/ComfyUI path                    $0 API
4. FLOW_SUBSCRIPTION   Google Flow/Veo subscription packet       $0 incremental accounting
5. CHEAP_CLOUD         separately billed API                     disabled by default
6. HERO_CLOUD          premium separately billed API             disabled by default
```

Flow/local costs are configurable accounting assumptions, not claims about provider billing.

## Quick start — Windows

```powershell
git clone https://github.com/BradyLoreeVillianyLabs/NarrateAnimateAwesomeGreat.git
cd NarrateAnimateAwesomeGreat

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[whisper,mcp,studio,dev]"

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
storyforge prompts projects\my-story
```

`--whisper` now performs real faster-whisper narration alignment and stores word timing in the manifest when available. Without it, StoryForge uses proportional timing against the narration duration.

## StoryForge Studio — graphical timeline

Start the local GUI:

```powershell
storyforge studio
```

or:

```powershell
storyforge-studio
```

Default address:

```text
http://127.0.0.1:8766
```

Studio provides:

- proportional scene tiles organized on the narration timeline
- filmstrip view for rapid visual assembly
- narration playback; selecting a scene seeks to its start time
- guide-image preview and drag/file upload
- generated-video preview/import
- story-text editing
- scene importance and motion-complexity controls
- automatic Director route display
- persistent human route override
- per-scene generation prompt editor
- one-click Flow packet creation
- project validation and Director refresh
- final render trigger

Studio edits the **same `manifest.json`, prompts and assets** used by CLI, Codex, Claude and MCP. There is no separate GUI database to drift out of sync.

See [`docs/STUDIO.md`](docs/STUDIO.md).

## Guide image → Flow/Veo workflow

From Studio, select a scene, add the guide image, tune the prompt and click **Create Flow Packet**.

Or from CLI:

```powershell
storyforge flow-pack projects\my-story --scenes 4,9,12
```

Packets look like:

```text
work/flow_packets/scene_004/
  keyframe.png
  prompt.txt
  context.json
  OUTPUT_NAME.txt
```

Generate the motion in Google Flow/Veo using the guide image, download it using the requested filename, then either import it through Studio or place it at:

```text
generated/scene_004.mp4
```

The renderer automatically substitutes it while preserving narration timing.

## Rendering

```powershell
storyforge render projects\my-story
```

The production renderer supports:

- generated-video substitution
- animated guide-image fallback
- per-scene camera motion
- burned SRT captions
- narration
- optional first music file under `music/`
- scene-timed SFX using filenames beginning with the scene number, e.g. `sfx/003_door.wav`
- NVENC final encode when NVIDIA is available
- H.264/AAC YouTube master

Output:

```text
projects/my-story/output/youtube_master.mp4
```

## Paid API safeguard

Separately billed generation is fail-closed:

```dotenv
STORYFORGE_ENABLE_PAID_API=0
```

Even if an API key is present, StoryForge refuses Veo/Runway API execution until this is deliberately changed to `1`. A second hard project-budget gate is also applied using `STORYFORGE_MAX_PROJECT_GENERATION_USD` and configured provider-per-second rates.

## MCP / VS Code agents

```powershell
storyforge-mcp
```

The MCP façade exposes safe project-level operations for listing/creating projects, planning, validation, Director routing, cost estimation, prompt/Flow packet export, dry-run generation and rendering.

MCP project paths are sandboxed to `STORYFORGE_PROJECTS_DIR`; API generation defaults to dry-run.

See:

- [`AGENTS.md`](AGENTS.md) — Codex builder contract
- [`CLAUDE.md`](CLAUDE.md) — Claude adversarial-review contract
- [`docs/MCP.md`](docs/MCP.md)
- [`docs/VS_CODE_AGENTS.md`](docs/VS_CODE_AGENTS.md)

## Project layout

```text
projects/my-story/
  story.txt
  narration.wav
  keyframes/
    001.png
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
    prompts/
    flow_packets/
    reviews/
  output/
    youtube_master.mp4
```

`work/manifest.json` is the canonical timeline. Example scene:

```json
{
  "id": 4,
  "start": 24.2,
  "end": 31.0,
  "duration": 6.8,
  "text": "Milo opened the tiny door.",
  "keyframe": "keyframes/004.png",
  "generated_video": "generated/scene_004.mp4",
  "motion": "push_in",
  "importance": 0.7,
  "motion_complexity": 2,
  "route_override": "FLOW_SUBSCRIPTION"
}
```

## Security boundaries

- `.env` is ignored; never commit credentials.
- Studio binds to localhost by default and has **no network authentication**; do not expose it publicly.
- Studio media/upload paths and MCP projects are sandboxed to the configured projects directory.
- Consumer Flow subscription use and separately billed Gemini API use are intentionally distinct paths.

## Development / verification

```powershell
pip install -e ".[dev]"
python -m compileall src
pytest -q
storyforge doctor
```

The project deliberately keeps FFmpeg as the final source of truth for timing and media assembly. AI models can be creative; the timeline is not allowed to be.
