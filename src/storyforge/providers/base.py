"""Provider-neutral video generation contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GenerationRequest:
    scene_id: int
    prompt: str
    output_path: Path
    image_path: Path | None = None
    duration: int = 6
    aspect_ratio: str = "16:9"
    resolution: str = "720p"


@dataclass
class GenerationResult:
    scene_id: int
    provider: str
    status: str
    output_path: Path | None = None
    remote_id: str | None = None
    message: str = ""


class VideoProvider(ABC):
    name = "base"

    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate one scene and place the finished clip at request.output_path."""
        raise NotImplementedError
