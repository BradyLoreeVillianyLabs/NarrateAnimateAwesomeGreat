"""Generate selected scenes through a provider adapter."""
from __future__ import annotations

from pathlib import Path
import os

from .util import load_json
from .providers import GenerationRequest, get_provider
from .config import Settings
from .flow_export import export_flow_packets

PAID_PROVIDERS = {"veo", "runway", "generic"}


def _paid_rate(provider: str) -> float:
    defaults = {"veo": 0.05, "runway": 0.05, "generic": 0.05}
    return float(os.getenv(f"STORYFORGE_{provider.upper()}_USD_PER_SECOND", defaults[provider]))


def _selected_duration(manifest: dict, scene_ids: set[int] | None) -> float:
    total = 0.0
    for scene in manifest.get("scenes", []):
        sid = int(scene["id"])
        if scene_ids and sid not in scene_ids:
            continue
        total += float(scene.get("duration", 0.0))
    return total


def generate_project(project: Path, provider_name: str, scene_ids: set[int] | None = None, dry_run: bool = False):
    project = Path(project)
    provider_name = provider_name.lower().strip()
    settings = Settings.from_env()

    if provider_name == "flow":
        # Flow subscription mode is packet export, not consumer-UI automation.
        return [export_flow_packets(project, scene_ids=scene_ids)]

    if provider_name in PAID_PROVIDERS and not settings.paid_api_enabled:
        raise RuntimeError(
            f"Paid provider '{provider_name}' is disabled. "
            "Use StoryForge Flow subscription packets or local/manual generation, "
            "or explicitly set STORYFORGE_ENABLE_PAID_API=1 in .env."
        )

    manifest = load_json(project / "work" / "manifest.json")
    if provider_name in PAID_PROVIDERS:
        estimated = round(_selected_duration(manifest, scene_ids) * _paid_rate(provider_name), 2)
        limit = float(os.getenv("STORYFORGE_MAX_PROJECT_GENERATION_USD", "20.00"))
        if estimated > limit and not dry_run:
            raise RuntimeError(
                f"Estimated {provider_name} generation cost ${estimated:.2f} exceeds "
                f"STORYFORGE_MAX_PROJECT_GENERATION_USD=${limit:.2f}. "
                "Raise the limit explicitly only after reviewing the batch."
            )

    provider = get_provider(provider_name)
    results = []
    for scene in manifest.get("scenes", []):
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
                "estimated_usd": round(float(scene["duration"]) * _paid_rate(provider_name), 2) if provider_name in PAID_PROVIDERS else 0.0,
            })
        else:
            result = provider.generate(req)
            results.append(result.__dict__)
    return results
