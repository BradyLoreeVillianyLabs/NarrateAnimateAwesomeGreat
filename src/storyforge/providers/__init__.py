"""Video provider registry."""
from .base import GenerationRequest, GenerationResult, VideoProvider


def get_provider(name: str) -> VideoProvider:
    key = name.lower().strip()
    if key == "veo":
        from .veo import VeoProvider
        return VeoProvider()
    if key == "runway":
        from .runway import RunwayProvider
        return RunwayProvider()
    if key in {"manual", "filesystem"}:
        from .manual import ManualProvider
        return ManualProvider()
    raise ValueError(f"Unknown provider: {name}. Supported: veo, runway, manual")


__all__ = ["GenerationRequest", "GenerationResult", "VideoProvider", "get_provider"]
