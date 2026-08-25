from .base import VideoProvider, GenerationRequest, GenerationResult


class ManualProvider(VideoProvider):
    """No-cost adapter: exports work for a human/UI workflow instead of calling an API."""
    name = "manual"

    def configured(self) -> bool:
        return True

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if request.output_path.exists():
            return GenerationResult(request.scene_id, self.name, "complete", request.output_path)
        return GenerationResult(
            request.scene_id,
            self.name,
            "awaiting_manual_generation",
            request.output_path,
            message="Generate the scene externally and save it at the requested output path.",
        )
