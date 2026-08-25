"""Environment and project configuration for StoryForge."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_environment(start: Path | None = None) -> None:
    if load_dotenv is None:
        return
    root = Path(start or Path.cwd())
    load_dotenv(root / ".env", override=False)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    raw = env(name, "1" if default else "0").lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    projects_dir: Path
    default_provider: str
    default_resolution: str
    aspect_ratio: str
    max_parallel: int
    poll_seconds: int
    use_flow_subscription: bool
    paid_api_enabled: bool

    @classmethod
    def from_env(cls) -> "Settings":
        load_environment()
        return cls(
            projects_dir=Path(env("STORYFORGE_PROJECTS_DIR", "projects")),
            default_provider=env("STORYFORGE_DEFAULT_PROVIDER", "flow"),
            default_resolution=env("STORYFORGE_DEFAULT_RESOLUTION", "720p"),
            aspect_ratio=env("STORYFORGE_DEFAULT_ASPECT_RATIO", "16:9"),
            max_parallel=max(1, int(env("STORYFORGE_MAX_PARALLEL_GENERATIONS", "1"))),
            poll_seconds=max(1, int(env("STORYFORGE_POLL_SECONDS", "10"))),
            use_flow_subscription=env_bool("STORYFORGE_USE_FLOW_SUBSCRIPTION", True),
            paid_api_enabled=env_bool("STORYFORGE_ENABLE_PAID_API", False),
        )


def masked_provider_status() -> dict[str, bool]:
    """Return capability/presence only. Never print or return secret values."""
    load_environment()
    return {
        "flow_subscription": env_bool("STORYFORGE_USE_FLOW_SUBSCRIPTION", True),
        "paid_api_enabled": env_bool("STORYFORGE_ENABLE_PAID_API", False),
        "veo_api_key_present": bool(env("GEMINI_API_KEY")),
        "runway_key_present": bool(env("RUNWAYML_API_SECRET")),
        "generic_key_present": bool(env("GENERIC_VIDEO_API_URL") and env("GENERIC_VIDEO_API_KEY")),
        "comfyui": bool(env("COMFYUI_URL")),
    }
