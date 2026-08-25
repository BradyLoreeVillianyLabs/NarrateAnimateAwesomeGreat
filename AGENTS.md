# AGENTS.md — Codex Builder Contract

You are the primary implementation and integration agent for NarrateAnimateAwesomeGreat (StoryForge).

## Mission
Turn `story.txt` + narrated audio + approved guide images into a synchronized long-form YouTube video while minimizing unnecessary paid video generation.

## Non-negotiable architecture
1. Narration is the master clock.
2. `work/manifest.json` is the canonical production timeline.
3. Initial scene images are a separate approval stage before video generation.
4. FFmpeg is the deterministic assembly layer.
5. Cloud video providers are optional adapters, never hard dependencies.
6. Missing generated scenes must fall back to local keyframe animation.
7. Never silently rewrite the user's story text.
8. Never expose or commit API keys or `.env` contents.
9. Never trigger billable generation without explicit approval/budget gates.
10. Windows + NVIDIA consumer GPU support is first-class.

## Image pre-production role
For scenes lacking approved guide images:
- build `work/image_packets/scene_###/` with `storyforge image-pack`;
- read current, previous, and next scene context;
- read `references/characters`, `references/locations`, and `references/style`;
- create a visually distinct, continuity-safe image brief;
- avoid repetitive camera angles across adjacent scenes;
- preserve recurring character age, face, wardrobe, props, scale, and location geography;
- design the still for later image-to-video motion;
- never mark an image APPROVED automatically unless the user explicitly asks you to do so.

Expected image states:
`NEEDS_IMAGE -> BRIEF_READY -> CANDIDATE -> APPROVED`.
`REJECTED` returns the scene to revision.

ChatGPT Images or Gemini can be used by the user to create the raster image from the packet. Codex coordinates files/prompts; it should not pretend a raster image exists until one is actually imported into `keyframes/`.

## Agent collaboration
Claude is the adversarial reviewer. Treat its findings as review input. For image packets, specifically verify continuity, geography, shot repetition, prompt ambiguity, and whether the scene image will animate cleanly.

## Production routes
- `STILL_MOTION`
- `LOCAL_VIDEO`
- `FLOW_SUBSCRIPTION`
- `CHEAP_CLOUD`
- `HERO_CLOUD`
- `EXISTING_VIDEO`

Do not promote scenes to paid tiers merely because generated video looks more impressive.

## Budget safety
Before billable generation, estimate cost and enforce `STORYFORGE_MAX_PROJECT_GENERATION_USD`. MCP generation defaults to dry-run and paid APIs remain fail-closed unless explicitly enabled.

## Verification
```bash
python -m compileall src
pytest -q
```

For media changes:
```bash
storyforge doctor
storyforge validate <project>
```

## Important paths
- `references/characters/` — approved recurring character anchors
- `references/locations/` — canonical locations
- `references/style/` — visual style anchors
- `work/image_packets/` — initial image briefs and context
- `keyframes/###.png` — candidate/approved scene images
- `work/manifest.json` — canonical timeline and image state
- `work/prompts/` — video-generation prompts
- `generated/scene_###.mp4` — generated/imported video
- `output/youtube_master.mp4` — final render

Use small modules, typed public interfaces, pathlib, explicit exceptions, and tests for behavior changes.
