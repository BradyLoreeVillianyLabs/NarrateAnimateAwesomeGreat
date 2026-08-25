"""Create and manage pre-production image packets for automatically separated scenes."""
from __future__ import annotations

from pathlib import Path
import json
import shutil

from .util import load_json, save_json

IMAGE_STATES = {"NEEDS_IMAGE", "BRIEF_READY", "CANDIDATE", "APPROVED", "REJECTED"}


def _manifest(project: Path) -> tuple[Path, dict]:
    path = Path(project) / "work" / "manifest.json"
    if not path.exists():
        raise FileNotFoundError("work/manifest.json not found; run storyforge plan first")
    return path, load_json(path)


def _reference_inventory(project: Path) -> dict:
    root = Path(project) / "references"
    out = {"characters": [], "locations": [], "style": []}
    for category in out:
        d = root / category
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".md", ".txt", ".json"}:
                out[category].append(p.relative_to(project).as_posix())
    return out


def _scene_context(scenes: list[dict], index: int) -> dict:
    return {
        "previous": scenes[index - 1].get("text", "") if index > 0 else "",
        "current": scenes[index].get("text", ""),
        "next": scenes[index + 1].get("text", "") if index + 1 < len(scenes) else "",
    }


def _default_prompt(scene: dict, context: dict, refs: dict) -> str:
    reference_lines = []
    for category, files in refs.items():
        if files:
            reference_lines.append(f"{category.upper()}:\n" + "\n".join(f"- {x}" for x in files))
    references = "\n\n".join(reference_lines) or "No canonical reference files have been added yet. Preserve established visual continuity from approved neighboring scenes."
    return f"""Create a single 16:9 landscape guide image for a children's long-form story video.

SCENE {int(scene['id']):03}
Narration time: {float(scene.get('start', 0)):.2f}s to {float(scene.get('end', 0)):.2f}s
Target visual hold: {float(scene.get('duration', 0)):.2f}s

STORY MOMENT
{scene.get('text', '').strip()}

NEIGHBORING CONTEXT
Previous: {context['previous'] or '(opening scene)'}
Next: {context['next'] or '(final scene)'}

CANONICAL REFERENCES
{references}

ART DIRECTION
- preserve recurring character identity, facial features, age, wardrobe, props and scale
- preserve location geography and recurring object placement
- make this composition visually distinct from neighboring scenes
- choose an intentional cinematic shot size and camera angle appropriate to the story beat
- compose for later image-to-video animation: clear subject silhouette, usable depth, uncluttered edges, room for subtle camera motion
- favor strong children's storybook readability and emotional clarity
- no printed words, captions, speech bubbles, watermarks or logos
- avoid malformed hands, duplicated subjects, disappearing props and accidental costume changes
- do not introduce characters or objects not supported by the story/context

OUTPUT
One polished 16:9 guide image suitable as the first-frame/reference image for later video generation.
"""


def create_image_packets(project: Path, scene_ids: set[int] | None = None, overwrite: bool = False) -> dict:
    project = Path(project)
    manifest_path, manifest = _manifest(project)
    scenes = manifest.get("scenes", [])
    refs = _reference_inventory(project)
    root = project / "work" / "image_packets"
    root.mkdir(parents=True, exist_ok=True)
    created = []

    for index, scene in enumerate(scenes):
        sid = int(scene["id"])
        if scene_ids and sid not in scene_ids:
            continue
        packet = root / f"scene_{sid:03}"
        packet.mkdir(parents=True, exist_ok=True)
        context = _scene_context(scenes, index)
        prompt_path = packet / "image_prompt.md"
        if overwrite or not prompt_path.exists():
            prompt_path.write_text(_default_prompt(scene, context, refs), encoding="utf-8")
        (packet / "scene.json").write_text(json.dumps({
            "scene_id": sid,
            "start": scene.get("start"),
            "end": scene.get("end"),
            "duration": scene.get("duration"),
            "text": scene.get("text", ""),
            "previous_scene_text": context["previous"],
            "next_scene_text": context["next"],
            "references": refs,
            "expected_output": f"keyframes/{sid:03}.png",
        }, indent=2), encoding="utf-8")
        (packet / "OUTPUT_NAME.txt").write_text(f"{sid:03}.png\n", encoding="utf-8")
        scene.setdefault("image_state", "BRIEF_READY")
        created.append(packet.relative_to(project).as_posix())

    save_json(manifest_path, manifest)
    index = {"project": project.name, "packets": created, "references": refs}
    (root / "INDEX.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def set_image_state(project: Path, scene_id: int, state: str) -> dict:
    if state not in IMAGE_STATES:
        raise ValueError(f"Unknown image state: {state}")
    manifest_path, manifest = _manifest(project)
    for scene in manifest.get("scenes", []):
        if int(scene.get("id", -1)) == int(scene_id):
            scene["image_state"] = state
            save_json(manifest_path, manifest)
            return scene
    raise KeyError(f"Scene {scene_id} not found")


def save_reference(project: Path, category: str, name: str, source: Path) -> Path:
    if category not in {"characters", "locations", "style"}:
        raise ValueError("Reference category must be characters, locations, or style")
    safe_name = "".join(c for c in name.strip() if c.isalnum() or c in {"-", "_", " "}).strip().replace(" ", "-")
    if not safe_name:
        raise ValueError("Reference name is empty")
    source = Path(source)
    dst_dir = Path(project) / "references" / category / safe_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / ("master" + source.suffix.lower())
    shutil.copy2(source, dst)
    return dst
