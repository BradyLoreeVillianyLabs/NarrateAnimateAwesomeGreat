# Video providers

StoryForge separates **timeline/rendering** from **video generation**. A provider only has to turn one `GenerationRequest` into `generated/scene_###.mp4`.

## Why this matters

Cloud video APIs change quickly. The narration, scene manifest, captions and FFmpeg renderer should not break because a vendor renamed an endpoint.

## Google Veo

Install:

```bash
pip install -e '.[veo]'
```

Configure `.env`:

```dotenv
GEMINI_API_KEY=your_key_here
VEO_MODEL=veo-3.1-generate-preview
VEO_RESOLUTION=720p
VEO_ASPECT_RATIO=16:9
```

Generate selected scenes:

```bash
storyforge generate projects/my-story --provider veo --scenes 2,4,7
```

Important: a paid Gemini consumer subscription does not automatically mean Gemini API usage is included. Treat API billing/quotas separately and verify the current Google AI Studio/API terms before a large batch.

## Runway

Install:

```bash
pip install -e '.[runway]'
```

Configure:

```dotenv
RUNWAYML_API_SECRET=your_secret_here
RUNWAY_MODEL=gen4_turbo
```

The adapter is intentionally isolated. Until a pinned SDK integration test is present, StoryForge reports the installed SDK state rather than silently spending credits against an unverified request schema.

## Manual / subscription UI mode

This is important for subscriptions that give you interactive video generation but no bundled API credits.

```bash
storyforge generate projects/my-story --provider manual
```

Generate the requested shots in the provider UI, then save/download each result as:

```text
projects/my-story/generated/scene_001.mp4
projects/my-story/generated/scene_002.mp4
```

Re-run `storyforge render`. The generated clips automatically replace local still animation for those scenes.

## Local Wan / ComfyUI

StoryForge uses a filesystem contract rather than forcing ComfyUI into the Python process. Configure `COMFYUI_URL` and optionally `WAN_WORKFLOW_JSON`. A future ComfyUI adapter can submit workflow JSON and copy finished clips into `generated/` without modifying the renderer.

## Adding another provider

Implement `VideoProvider` from `src/storyforge/providers/base.py`:

```python
class MyProvider(VideoProvider):
    name = "mine"

    def configured(self) -> bool:
        ...

    def generate(self, request: GenerationRequest) -> GenerationResult:
        # write final MP4 to request.output_path
        ...
```

Then register it in `providers/__init__.py`.

Never expose API keys in manifests, logs, MCP results or generation queue CSV files.
