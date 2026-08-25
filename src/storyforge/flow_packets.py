"""Export selected scenes as Google Flow/Veo subscription production packets."""
from __future__ import annotations

from pathlib import Path
import json
import shutil

from .util import load_json

DEFAULT_PROMPT = """Image-to-video for a children's illustrated story.\n\nPreserve the supplied guide image exactly as the visual reference for character identity, wardrobe, proportions, palette, props, environment and illustration style.\n\nStory moment:\n{scene_text}\n\nAnimate with restrained, natural motion. Prefer one continuous shot, gentle camera movement and subtle environmental motion. No text, captions, morphing, costume changes, duplicated characters or unnecessary cuts.\n\nTarget scene duration: {duration:.1f} seconds.\n"""


def export_flow_packets(project: Path, scene_ids: set[int] | None = None) -> list[Path]:
    project = Path(project)
    manifest_path = project / "work" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("work/manifest.json not found; run storyforge plan first")
    manifest = load_json(manifest_path)
    root = project / "work" / "flow_packets"
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for scene in manifest.get("scenes", []):
        sid = int(scene["id"])
        if scene_ids and sid not in scene_ids:
            continue
        packet = root / f"scene_{sid:03}"
        packet.mkdir(parents=True, exist_ok=True)
        prompt_file = project / "work" / "prompts" / f"scene_{sid:03}.txt"
        prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else DEFAULT_PROMPT.format(
            scene_text=scene.get("text", ""), duration=float(scene.get("duration", 6.0))
        )
        (packet / "prompt.txt").write_text(prompt, encoding="utf-8")
        (packet / "OUTPUT_NAME.txt").write_text(f"scene_{sid:03}.mp4\n", encoding="utf-8")
        context = {
            "scene_id": sid,
            "start": scene.get("start"),
            "end": scene.get("end"),
            "duration": scene.get("duration"),
            "story_text": scene.get("text", ""),
            "importance": scene.get("importance", 0.5),
            "motion_complexity": scene.get("motion_complexity"),
            "route_override": scene.get("route_override"),
            "destination": scene.get("generated_video", f"generated/scene_{sid:03}.mp4"),
            "instructions": "Use the cheapest suitable Flow/Veo subscription tier first. Keep the guide image as the continuity anchor.",
        }
        (packet / "context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
        key = scene.get("keyframe")
        if key:
            src = project / key
            if src.is_file():
                shutil.copy2(src, packet / f"keyframe{src.suffix.lower()}")
        created.append(packet)
    return created
