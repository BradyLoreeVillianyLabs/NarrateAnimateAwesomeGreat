"""Environment and project configuration for StoryForge."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:  # core remains usable without optional cloud dependencies
    load_dotenv = None


def load_environment(start: Path | None = None) -> None:
    """Load .env without overwriting environment variables already supplied by the host."""
    if load_dotenv is None:
        return
    root = Path(start or Path.cwd())
    load_dotenv(root / ".env", override=False)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    projects_dir: Path
    default_provider: str
    default_resolution: str
    aspect_ratio: str
    max_parallel: int
    poll_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_environment()
        return cls(
            projects_dir=Path(env("STORYFORGE_PROJECTS_DIR", "projects")),
            default_provider=env("STORYFORGE_DEFAULT_PROVIDER", "veo"),
            default_resolution=env("STORYFORGE_DEFAULT_RESOLUTION", "720p"),
            aspect_ratio=env("STORYFORGE_DEFAULT_ASPECT_RATIO", "16:9"),
            max_parallel=max(1, int(env("STORYFORGE_MAX_PARALLEL_GENERATIONS", "1"))),
            poll_seconds=max(1, int(env("STORYFORGE_POLL_SECONDS", "10"))),
        )


def masked_provider_status() -> dict[str, bool]:
    """Return presence only. Never print or return secret values."""
    load_environment()
    return {
        "veo": bool(env("GEMINI_API_KEY")),
        "runway": bool(env("RUNWAYML_API_SECRET")),
        "generic": bool(env("GENERIC_VIDEO_API_URL") and env("GENERIC_VIDEO_API_KEY")),
        "comfyui": bool(env("COMFYUI_URL")),
    }
