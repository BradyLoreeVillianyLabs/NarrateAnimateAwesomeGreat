"""Runway adapter. Kept isolated so SDK changes cannot break the core renderer."""
from __future__ import annotations

from .base import VideoProvider, GenerationRequest, GenerationResult
from ..config import env, load_environment


class RunwayProvider(VideoProvider):
    name = "runway"

    def __init__(self):
        load_environment()
        self.secret = env("RUNWAYML_API_SECRET")
        self.model = env("RUNWAY_MODEL", "gen4_turbo")

    def configured(self) -> bool:
        return bool(self.secret)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.configured():
            return GenerationResult(request.scene_id, self.name, "not_configured", message="Set RUNWAYML_API_SECRET")
        try:
            from runwayml import RunwayML
        except ImportError:
            return GenerationResult(request.scene_id, self.name, "dependency_missing", message="pip install -e '.[runway]'")

        # Runway's SDK/API evolves quickly. This adapter deliberately validates the
        # installed SDK at runtime rather than coupling StoryForge's renderer to it.
        client = RunwayML(api_key=self.secret)
        if not hasattr(client, "image_to_video"):
            return GenerationResult(request.scene_id, self.name, "sdk_incompatible", message="Installed Runway SDK has no image_to_video endpoint; see docs/PROVIDERS.md")
        if not request.image_path:
            return GenerationResult(request.scene_id, self.name, "image_required", message="Gen-4 Turbo workflow requires a keyframe")
        return GenerationResult(
            request.scene_id, self.name, "adapter_ready",
            request.output_path,
            message="Provider credentials and SDK detected. Use the current Runway task schema documented in docs/PROVIDERS.md or manual mode until pinned integration tests are added."
        )
