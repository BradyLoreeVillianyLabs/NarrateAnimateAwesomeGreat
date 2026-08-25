"""Export Google Flow/Veo subscription-ready scene packets.

This module does not automate the consumer Flow UI. It prepares deterministic
scene folders that can be used manually with a paid Google AI subscription,
then imported back into StoryForge by filename convention.
"""
from __future__ import annotations

from pathlib import Path
import json
import shutil

from .util import load_json
from .director import route_project


def _prompt(scene: dict) -> str:
    return f"""Frames-to-video task for a children's illustrated story.

Use the supplied keyframe as the visual authority.
Preserve character identity, face, clothing, proportions, environment, props,
palette, lighting, illustration style and overall composition.

STORY MOMENT:
{scene.get('text','').strip()}

ANIMATION DIRECTION:
- create natural motion that serves this exact story moment
- keep motion restrained unless the story explicitly demands action
- use gentle cinematic camera movement
- preserve continuity with the source frame
- no scene cuts unless explicitly required
- no on-screen text or subtitles
- no new characters unless explicitly required
- no morphing, costume changes, duplicated limbs or disappearing props

OUTPUT:
- landscape 16:9
- target duration: {float(scene.get('duration', 6.0)):.1f} seconds
- use the cheapest practical Veo/Flow tier first
- prefer the longest available clip duration that does not exceed the scene need
- upscale in Flow if included at no additional credit cost
"""


def export_flow_packets(project: Path, include_routes: set[str] | None = None) -> dict:
    project = Path(project)
    manifest = load_json(project / "work" / "manifest.json")
    decisions = {d.scene_id: d for d in route_project(project, prefer_local=True)}
    include_routes = include_routes or {"FLOW_SUBSCRIPTION", "HERO_CLOUD"}

    root = project / "work" / "flow_packets"
    root.mkdir(parents=True, exist_ok=True)
    created = []

    for scene in manifest.get("scenes", []):
        sid = int(scene["id"])
        decision = decisions[sid]
        if decision.route not in include_routes:
            continue
        packet = root / f"scene_{sid:03}"
        packet.mkdir(parents=True, exist_ok=True)

        keyframe = project / str(scene.get("keyframe", "")) if scene.get("keyframe") else None
        copied_keyframe = None
        if keyframe and keyframe.is_file():
            copied_keyframe = packet / ("keyframe" + keyframe.suffix.lower())
            shutil.copy2(keyframe, copied_keyframe)

        (packet / "prompt.txt").write_text(_prompt(scene), encoding="utf-8")
        (packet / "OUTPUT_NAME.txt").write_text(f"scene_{sid:03}.mp4\n", encoding="utf-8")
        context = {
            "scene_id": sid,
            "start": scene.get("start"),
            "end": scene.get("end"),
            "duration": scene.get("duration"),
            "route": decision.route,
            "reason": decision.reason,
            "story_text": scene.get("text", ""),
            "keyframe": copied_keyframe.name if copied_keyframe else None,
            "return_to": f"generated/scene_{sid:03}.mp4",
        }
        (packet / "context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
        created.append(str(packet))

    index = {
        "project": str(project),
        "packets": created,
        "instructions": [
            "Open each packet in scene order.",
            "Upload keyframe.* and use prompt.txt in Google Flow/Veo.",
            "Use the cheapest practical Flow tier first.",
            "Download the result using OUTPUT_NAME.txt.",
            "Copy it to the project's generated/ folder.",
            "Re-run storyforge validate and storyforge render.",
        ],
    }
    (root / "INDEX.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index
