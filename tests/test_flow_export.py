import json
from pathlib import Path

from storyforge.flow_export import export_flow_packets


def test_targeted_flow_packet_exports_any_selected_scene(tmp_path, monkeypatch):
    project = tmp_path / "movie"
    (project / "work" / "prompts").mkdir(parents=True)
    (project / "keyframes").mkdir()
    (project / "generated").mkdir()
    (project / "narration.wav").write_bytes(b"n")
    (project / "keyframes" / "001.png").write_bytes(b"image")
    manifest = {
        "narration": "narration.wav",
        "duration": 5.0,
        "scenes": [{
            "id": 1, "start": 0.0, "end": 5.0, "duration": 5.0,
            "text": "A still scene.", "keyframe": "keyframes/001.png",
            "generated_video": "generated/scene_001.mp4", "importance": 0.2,
        }],
    }
    (project / "work" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setenv("STORYFORGE_USE_FLOW_SUBSCRIPTION", "1")

    result = export_flow_packets(project, scene_ids={1})
    packet = project / "work" / "flow_packets" / "scene_001"
    assert str(packet) in result["packets"]
    assert (packet / "prompt.txt").exists()
    assert (packet / "context.json").exists()
    assert (packet / "OUTPUT_NAME.txt").read_text().strip() == "scene_001.mp4"
