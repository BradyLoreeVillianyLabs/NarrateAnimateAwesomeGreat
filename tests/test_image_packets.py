import json
from pathlib import Path

from storyforge.image_packets import create_image_packets, set_image_state


def make_project(tmp_path: Path):
    p = tmp_path / "movie"
    (p / "work").mkdir(parents=True)
    (p / "references" / "characters" / "milo").mkdir(parents=True)
    (p / "references" / "characters" / "milo" / "master.png").write_bytes(b"x")
    manifest = {
        "duration": 10.0,
        "scenes": [
            {"id": 1, "start": 0.0, "end": 5.0, "duration": 5.0, "text": "Milo enters the garden."},
            {"id": 2, "start": 5.0, "end": 10.0, "duration": 5.0, "text": "He opens the tiny door."},
        ],
    }
    (p / "work" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return p


def test_image_packets_include_neighbor_context_and_refs(tmp_path):
    p = make_project(tmp_path)
    result = create_image_packets(p)
    assert len(result["packets"]) == 2
    prompt = (p / "work" / "image_packets" / "scene_002" / "image_prompt.md").read_text(encoding="utf-8")
    assert "Milo enters the garden" in prompt
    assert "references/characters/milo/master.png" in prompt
    manifest = json.loads((p / "work" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenes"][0]["image_state"] == "BRIEF_READY"


def test_image_state_can_be_approved(tmp_path):
    p = make_project(tmp_path)
    create_image_packets(p)
    scene = set_image_state(p, 1, "APPROVED")
    assert scene["image_state"] == "APPROVED"
    manifest = json.loads((p / "work" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenes"][0]["image_state"] == "APPROVED"
