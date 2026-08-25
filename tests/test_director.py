import json
from pathlib import Path

from storyforge.director import inspect_project, estimate_project


def make_project(tmp_path: Path):
    p = tmp_path / "movie"
    (p / "work").mkdir(parents=True)
    (p / "keyframes").mkdir()
    (p / "generated").mkdir()
    (p / "narration.wav").write_bytes(b"placeholder")
    (p / "keyframes" / "001.png").write_bytes(b"placeholder")
    manifest = {
        "narration": "narration.wav",
        "duration": 10.0,
        "scenes": [
            {"id": 1, "start": 0.0, "end": 5.0, "duration": 5.0, "text": "Milo looks at the moon.", "keyframe": "keyframes/001.png", "generated_video": "generated/scene_001.mp4", "importance": 0.5},
            {"id": 2, "start": 5.0, "end": 10.0, "duration": 5.0, "text": "Milo runs and jumps across the bridge.", "keyframe": "keyframes/001.png", "generated_video": "generated/scene_002.mp4", "importance": 0.9},
        ],
    }
    (p / "work" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return p


def test_inspection_accepts_valid_project(tmp_path):
    p = make_project(tmp_path)
    result = inspect_project(p)
    assert result.valid
    assert result.scene_count == 2
    assert result.keyframed_scenes == 2


def test_director_prefers_free_still_for_simple_scene(tmp_path):
    p = make_project(tmp_path)
    result = estimate_project(p)
    first = result["decisions"][0]
    assert first["route"] == "STILL_MOTION"
    assert first["estimated_usd"] == 0.0


def test_estimator_has_budget_gate(tmp_path, monkeypatch):
    p = make_project(tmp_path)
    monkeypatch.setenv("STORYFORGE_MAX_PROJECT_GENERATION_USD", "0.01")
    result = estimate_project(p, prefer_local=False)
    assert "within_budget" in result
    assert result["budget_limit_usd"] == 0.01
