# Initial Image Production Workflow

StoryForge treats scene images as a formal pre-production stage before image-to-video generation.

## Pipeline

```text
story + narration
      ↓
automatic scene split
      ↓
image packet
      ↓
Codex brief preparation
      ↓
Claude continuity review
      ↓
ChatGPT Images / Gemini image generation
      ↓
Studio candidate import
      ↓
human approval
      ↓
Flow/Veo or local I2V
```

## Commands

Create briefs for every scene:

```bash
storyforge image-pack projects/my-story
```

Selected scenes:

```bash
storyforge image-pack projects/my-story --scenes 1,4,7
```

Rebuild generated prompts from current references/context:

```bash
storyforge image-pack projects/my-story --overwrite
```

Packets are stored at:

```text
work/image_packets/scene_###/
  image_prompt.md
  scene.json
  OUTPUT_NAME.txt
```

## References

Canonical visual anchors live under:

```text
references/
  characters/
    milo/master.png
  locations/
    garden/master.png
  style/
    storybook/master.png
```

Add these through StoryForge Studio or directly on disk. Re-run `image-pack --overwrite` when reference material changes substantially.

## Image states

`NEEDS_IMAGE` — no approved visual exists.

`BRIEF_READY` — prompt/context packet has been prepared.

`CANDIDATE` — a guide image has been imported but not approved.

`APPROVED` — human-approved image may be used as the canonical scene guide for video generation.

`REJECTED` — candidate failed review and should be replaced/revised.

Uploading a keyframe in Studio automatically marks it `CANDIDATE`; approval remains a separate action.

## ChatGPT / Gemini workflow

For each scene, copy `image_prompt.md`, attach the appropriate character/location/style reference images, generate a 16:9 landscape image, and save/import it using the expected output filename. StoryForge does not scrape or automate consumer AI subscription interfaces.

The image packet intentionally includes neighboring scene context so a model can understand what must remain continuous and what should change.

## Studio

`storyforge studio` provides:

- Build Image Brief (single scene)
- Build Image Briefs (whole project)
- Copy Image Prompt
- candidate image upload
- Approve Image
- Reject Image
- reference-library upload
- approved-image count
- scene image-state badges

## Agent responsibilities

Codex is the production coordinator. It can build/refine packets and verify file/state consistency, but it should not claim an image was generated or approved unless the actual asset/state exists.

Claude is the continuity/art-direction reviewer. It should challenge repetitive compositions, character drift, geography errors, prompt ambiguity, and images that will animate poorly.

Human approval is the final authority for guide images.
