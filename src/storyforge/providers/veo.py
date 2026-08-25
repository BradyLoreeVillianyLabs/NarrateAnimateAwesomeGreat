"""Google Veo adapter using the official google-genai SDK."""
from __future__ import annotations

import os
import time
from .base import VideoProvider, GenerationRequest, GenerationResult
from ..config import env, load_environment


class VeoProvider(VideoProvider):
    name = "veo"

    def __init__(self):
        load_environment()
        self.api_key = env("GEMINI_API_KEY")
        self.model = env("VEO_MODEL", "veo-3.1-generate-preview")
        self.poll_seconds = int(env("STORYFORGE_POLL_SECONDS", "10"))

    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.configured():
            return GenerationResult(request.scene_id, self.name, "not_configured", message="Set GEMINI_API_KEY")
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return GenerationResult(request.scene_id, self.name, "dependency_missing", message="pip install -e '.[veo]'")

        client = genai.Client(api_key=self.api_key)
        kwargs = {"model": self.model, "prompt": request.prompt}
        if request.image_path:
            # Official SDK accepts an Image object for image-to-video requests.
            kwargs["image"] = types.Image.from_file(location=str(request.image_path))
        kwargs["config"] = types.GenerateVideosConfig(
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
        )
        operation = client.models.generate_videos(**kwargs)
        while not operation.done:
            time.sleep(self.poll_seconds)
            operation = client.operations.get(operation)

        response = operation.response
        videos = getattr(response, "generated_videos", None) or []
        if not videos:
            return GenerationResult(request.scene_id, self.name, "failed", remote_id=getattr(operation, "name", None), message="No video returned")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        video = videos[0].video
        client.files.download(file=video)
        video.save(str(request.output_path))
        return GenerationResult(request.scene_id, self.name, "complete", request.output_path, getattr(operation, "name", None))
