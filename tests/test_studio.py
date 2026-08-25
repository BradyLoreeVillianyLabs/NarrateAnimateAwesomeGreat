import json
from pathlib import Path

from fastapi.testclient import TestClient


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "projects" / "movie"
    (project / "work" / "prompts").mkdir(parents=True)
    (project / "keyframes").mkdir()
    (project / "generated").mkdir()
    (project / "narration.wav").write_bytes(b"placeholder")
    manifest = {
        "title": "Movie",
        "narration": "narration.wav",
        "duration": 8.0,
        "fps": 30,
        "resolution": [1920, 1080],
        "scenes": [{
            "id": 1,
            "start": 0.0,
            "end": 8.0,
            "duration": 8.0,
            "text": "A quiet scene.",
            "keyframe": None,
            "generated_video": "generated/scene_001.mp4",
            "importance": 0.5,
        }],
    }
    (project / "work" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return project


def test_timeline_and_scene_patch(tmp_path, monkeypatch):
    make_project(tmp_path)
    monkeypatch.setenv("STORYFORGE_PROJECTS_DIR", str(tmp_path / "projects"))
    from storyforge.studio import app
    client = TestClient(app)

    response = client.get("/api/projects/movie/timeline")
    assert response.status_code == 200
    assert response.json()["scenes"][0]["id"] == 1

    response = client.patch(
        "/api/projects/movie/scenes/1",
        json={"importance": 0.9, "motion_complexity": 4, "route_override": "FLOW_SUBSCRIPTION"},
    )
    assert response.status_code == 200
    scene = response.json()["scenes"][0]
    assert scene["importance"] == 0.9
    assert scene["route_override"] == "FLOW_SUBSCRIPTION"
    assert scene["decision"]["route"] == "FLOW_SUBSCRIPTION"


def test_keyframe_upload_updates_manifest(tmp_path, monkeypatch):
    project = make_project(tmp_path)
    monkeypatch.setenv("STORYFORGE_PROJECTS_DIR", str(tmp_path / "projects"))
    from storyforge.studio import app
    client = TestClient(app)

    response = client.post(
        "/api/projects/movie/scenes/1/keyframe",
        files={"file": ("guide.png", b"fake-png", "image/png")},
    )
    assert response.status_code == 200
    assert (project / "keyframes" / "001.png").exists()
    manifest = json.loads((project / "work" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenes"][0]["keyframe"] == "keyframes/001.png"


def test_path_traversal_is_rejected(tmp_path, monkeypatch):
    make_project(tmp_path)
    monkeypatch.setenv("STORYFORGE_PROJECTS_DIR", str(tmp_path / "projects"))
    from storyforge.studio import app
    client = TestClient(app)
    response = client.get("/api/projects/%2E%2E/timeline")
    assert response.status_code in {400, 404}
