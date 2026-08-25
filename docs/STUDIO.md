# StoryForge Studio

StoryForge Studio is the local visual storyboard/timeline interface for NarrateAnimateAwesomeGreat.

It is intentionally **not** a general-purpose nonlinear video editor. Narration already defines the master timeline, so Studio focuses on the tasks that matter to this production system: reviewing story beats, attaching guide images, importing generated clips, editing prompts, overriding scene routing, checking production state and launching deterministic renders.

## Install

```powershell
pip install -e ".[studio]"
```

For the normal development machine setup:

```powershell
pip install -e ".[whisper,mcp,studio,dev]"
```

## Start

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

The server is intentionally localhost-only by default. Studio has filesystem write access to StoryForge projects and does not currently provide user authentication. Do not bind it to a public/network interface without adding an authenticated reverse proxy or equivalent controls.

## Workflow

1. Create and plan a project with `storyforge init` and `storyforge plan`.
2. Launch Studio.
3. Select the project.
4. Review scenes in the proportional timeline or filmstrip.
5. Click a scene to open its inspector.
6. Add/replace a guide image. Studio stores it under `keyframes/` and updates `work/manifest.json` immediately.
7. Adjust importance, motion complexity or an explicit route override.
8. Edit the scene's generation prompt.
9. Create a Flow packet for that scene when needed.
10. Generate externally in Google Flow/Veo or locally.
11. Import the returned video into the same scene tile.
12. Validate/refresh the Director and render.

## Canonical state

Studio does not maintain a separate project database. It edits the same StoryForge files used by CLI, MCP, Codex and Claude:

```text
story.txt
work/manifest.json
work/prompts/scene_###.txt
keyframes/###.png
generated/scene_###.mp4
```

This is deliberate. An edit made in Studio is immediately visible to agents and CLI tools.

## Scene statuses

- `○` no guide image
- `◐` guide/keyframe available
- `◆` scene routed to Flow/local generation
- `▶` generated/imported video available

A generated video always takes precedence in the renderer. Removing/replacing that file allows the keyframe fallback to take over again.

## Route override

The Director normally chooses a route automatically. Studio can persist `route_override` in a scene when human judgment should win.

Supported routes:

```text
STILL_MOTION
LOCAL_VIDEO
FLOW_SUBSCRIPTION
CHEAP_CLOUD
HERO_CLOUD
EXISTING_VIDEO
```

`EXISTING_VIDEO` is normally determined by the presence of the scene video and should not be manually forced for a missing file.

Set the Studio dropdown back to `AUTO` to remove an override.

## API

Studio exposes a local FastAPI service. Interactive API documentation is available while running at:

```text
http://127.0.0.1:8766/api/docs
```

Important endpoint families:

```text
GET   /api/projects
GET   /api/projects/{project}/timeline
GET   /api/projects/{project}/inspect
POST  /api/projects/{project}/director
PATCH /api/projects/{project}/scenes/{scene}
PUT   /api/projects/{project}/scenes/{scene}/prompt
POST  /api/projects/{project}/scenes/{scene}/keyframe
POST  /api/projects/{project}/scenes/{scene}/generated
POST  /api/projects/{project}/scenes/{scene}/flow-packet
POST  /api/projects/{project}/render
```

Media serving and upload paths are sandboxed to `STORYFORGE_PROJECTS_DIR`.

## Why no React build step yet?

The first production version deliberately uses a zero-build static front end served by FastAPI. That gives Windows users a one-command install and avoids introducing Node/npm/Vite as another source of version drift.

If Studio grows into a much heavier editor (waveform editing, multitrack SFX placement, draggable scene boundaries, collaborative state), the static UI can be migrated to React/TypeScript without changing the backend API or manifest contract.
