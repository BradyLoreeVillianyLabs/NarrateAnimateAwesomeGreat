"""Production inspection, validation, scene routing and budget estimation."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os

from .util import load_json

ROUTES = {"STILL_MOTION", "LOCAL_VIDEO", "CHEAP_CLOUD", "HERO_CLOUD", "EXISTING_VIDEO"}


@dataclass
class SceneDecision:
    scene_id: int
    route: str
    reason: str
    duration: float
    importance: float
    motion_complexity: int
    estimated_usd: float


@dataclass
class ProjectInspection:
    project: str
    valid: bool
    errors: list[str]
    warnings: list[str]
    scene_count: int
    duration: float
    generated_scenes: int
    keyframed_scenes: int


def _manifest(project: Path) -> dict:
    path = project / "work" / "manifest.json"
    if not path.exists():
        raise FileNotFoundError("work/manifest.json not found; run storyforge plan first")
    return load_json(path)


def inspect_project(project: Path) -> ProjectInspection:
    project = Path(project)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        m = _manifest(project)
    except Exception as exc:
        return ProjectInspection(str(project), False, [str(exc)], [], 0, 0.0, 0, 0)

    narration = project / str(m.get("narration", ""))
    if not narration.exists():
        errors.append(f"Narration missing: {narration}")

    scenes = m.get("scenes", [])
    if not scenes:
        errors.append("Manifest contains no scenes")

    generated = keyframed = 0
    previous_end = 0.0
    for s in scenes:
        sid = s.get("id", "?")
        start = float(s.get("start", 0))
        end = float(s.get("end", 0))
        if end <= start:
            errors.append(f"Scene {sid}: end must be after start")
        if start + 0.075 < previous_end:
            errors.append(f"Scene {sid}: overlaps previous scene")
        previous_end = max(previous_end, end)
        gen = project / str(s.get("generated_video", ""))
        key = project / str(s.get("keyframe", "")) if s.get("keyframe") else None
        if gen.is_file():
            generated += 1
        if key and key.is_file():
            keyframed += 1
        if not gen.is_file() and not (key and key.is_file()):
            warnings.append(f"Scene {sid}: no generated clip or keyframe; renderer will use fallback")
        if not str(s.get("text", "")).strip():
            warnings.append(f"Scene {sid}: empty scene text")

    manifest_duration = float(m.get("duration", 0.0))
    if scenes and abs(float(scenes[-1].get("end", 0.0)) - manifest_duration) > 1.0:
        warnings.append("Last scene end differs from manifest duration by more than 1 second")

    return ProjectInspection(
        project=str(project), valid=not errors, errors=errors, warnings=warnings,
        scene_count=len(scenes), duration=manifest_duration,
        generated_scenes=generated, keyframed_scenes=keyframed,
    )


def _rate(route: str) -> float:
    defaults = {
        "STILL_MOTION": 0.0,
        "LOCAL_VIDEO": 0.0,
        "CHEAP_CLOUD": 0.05,
        "HERO_CLOUD": 0.15,
        "EXISTING_VIDEO": 0.0,
    }
    env = {
        "CHEAP_CLOUD": "STORYFORGE_CHEAP_CLOUD_USD_PER_SECOND",
        "HERO_CLOUD": "STORYFORGE_HERO_CLOUD_USD_PER_SECOND",
        "LOCAL_VIDEO": "STORYFORGE_LOCAL_VIDEO_USD_PER_SECOND",
    }
    if route in env:
        return float(os.getenv(env[route], defaults[route]))
    return defaults[route]


def _complexity(scene: dict) -> int:
    explicit = scene.get("motion_complexity")
    if explicit is not None:
        return max(1, min(5, int(explicit)))
    text = str(scene.get("text", "")).lower()
    action_words = (
        "run", "running", "jump", "fly", "flying", "fight", "dance", "chase",
        "fall", "swim", "climb", "ride", "explode", "transform", "crowd", "race",
    )
    score = 1 + sum(1 for word in action_words if word in text)
    return max(1, min(5, score))


def route_project(project: Path, prefer_local: bool = True) -> list[SceneDecision]:
    project = Path(project)
    m = _manifest(project)
    decisions: list[SceneDecision] = []
    for s in m.get("scenes", []):
        sid = int(s["id"])
        duration = float(s.get("duration", float(s["end"]) - float(s["start"])))
        importance = max(0.0, min(1.0, float(s.get("importance", 0.5))))
        complexity = _complexity(s)
        generated = project / str(s.get("generated_video", ""))
        keyframe = project / str(s.get("keyframe", "")) if s.get("keyframe") else None

        if generated.is_file():
            route, reason = "EXISTING_VIDEO", "generated/imported clip already exists"
        elif keyframe and keyframe.is_file() and complexity <= 2 and importance < 0.75:
            route, reason = "STILL_MOTION", "keyframe exists and motion demand is modest"
        elif prefer_local and keyframe and keyframe.is_file() and complexity <= 3:
            route, reason = "LOCAL_VIDEO", "moderate motion with a keyframe is suitable for local I2V"
        elif importance >= 0.85 or complexity >= 5:
            route, reason = "HERO_CLOUD", "high importance or very complex motion"
        else:
            route, reason = "CHEAP_CLOUD", "motion benefits from generated video but premium tier is unnecessary"

        decisions.append(SceneDecision(
            scene_id=sid, route=route, reason=reason, duration=round(duration, 3),
            importance=importance, motion_complexity=complexity,
            estimated_usd=round(duration * _rate(route), 4),
        ))
    return decisions


def estimate_project(project: Path, prefer_local: bool = True) -> dict:
    decisions = route_project(project, prefer_local=prefer_local)
    by_route: dict[str, dict] = {}
    for d in decisions:
        bucket = by_route.setdefault(d.route, {"scenes": 0, "seconds": 0.0, "estimated_usd": 0.0})
        bucket["scenes"] += 1
        bucket["seconds"] += d.duration
        bucket["estimated_usd"] += d.estimated_usd
    for bucket in by_route.values():
        bucket["seconds"] = round(bucket["seconds"], 3)
        bucket["estimated_usd"] = round(bucket["estimated_usd"], 2)
    total = round(sum(d.estimated_usd for d in decisions), 2)
    limit = float(os.getenv("STORYFORGE_MAX_PROJECT_GENERATION_USD", "20.00"))
    return {
        "estimated_usd": total,
        "budget_limit_usd": limit,
        "within_budget": total <= limit,
        "by_route": by_route,
        "decisions": [asdict(d) for d in decisions],
    }


def write_director_plan(project: Path, prefer_local: bool = True) -> Path:
    project = Path(project)
    data = estimate_project(project, prefer_local=prefer_local)
    out = project / "work" / "director_plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out
