"""Generate selected scenes through a provider adapter."""
from __future__ import annotations

from pathlib import Path
from .util import load_json
from .providers import GenerationRequest, get_provider
from .config import Settings
from .flow_export import export_flow_packets

PAID_PROVIDERS = {"veo", "runway", "generic"}


def generate_project(project: Path, provider_name: str, scene_ids: set[int] | None = None, dry_run: bool = False):
    project = Path(project)
    provider_name = provider_name.lower().strip()
    settings = Settings.from_env()

    if provider_name == "flow":
        # Flow subscription mode is packet export, not consumer-UI automation.
        return [export_flow_packets(project)]

    if provider_name in PAID_PROVIDERS and not settings.paid_api_enabled:
        raise RuntimeError(
            f"Paid provider '{provider_name}' is disabled. "
            "Use StoryForge Flow subscription packets or local/manual generation, "
            "or explicitly set STORYFORGE_ENABLE_PAID_API=1 in .env."
        )

    manifest = load_json(project / "work" / "manifest.json")
    provider = get_provider(provider_name)
    results = []
    for scene in manifest["scenes"]:
        sid = int(scene["id"])
        if scene_ids and sid not in scene_ids:
            continue
        output = project / scene["generated_video"]
        if output.exists():
            continue
        prompt_file = project / "work" / "prompts" / f"scene_{sid:03}.txt"
        prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else scene["text"]
        image = project / scene["keyframe"] if scene.get("keyframe") else None
        req = GenerationRequest(
            scene_id=sid,
            prompt=prompt,
            output_path=output,
            image_path=image if image and image.exists() else None,
            duration=max(1, round(float(scene["duration"]))),
        )
        if dry_run:
            results.append({
                "scene": sid,
                "provider": provider_name,
                "output": str(output),
                "keyframe": str(image or ""),
            })
        else:
            r = provider.generate(req)
            results.append(r.__dict__)
    return results
