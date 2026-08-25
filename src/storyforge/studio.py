"""Local StoryForge Studio web UI."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import mimetypes
import shutil
import webbrowser

from .config import Settings
from .director import inspect_project, estimate_project, write_director_plan, ROUTES
from .flow_export import export_flow_packets
from .image_packets import create_image_packets, set_image_state, save_reference, IMAGE_STATES
from .render import render
from .util import load_json, save_json

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError as exc:
    raise RuntimeError("Install Studio support with: pip install -e '.[studio]'") from exc

PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "studio_static"

app = FastAPI(title="StoryForge Studio", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ScenePatch(BaseModel):
    text: str | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    motion_complexity: int | None = Field(default=None, ge=1, le=5)
    route_override: str | None = None
    image_state: str | None = None


class PromptPatch(BaseModel):
    prompt: str


def _projects_root() -> Path:
    root = Settings.from_env().projects_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _project(name: str) -> Path:
    safe = Path(name).name
    if safe != name or safe in {"", ".", ".."}:
        raise HTTPException(400, "Invalid project name")
    root = _projects_root()
    path = (root / safe).resolve()
    if path.parent != root:
        raise HTTPException(400, "Invalid project path")
    if not path.exists():
        raise HTTPException(404, "Project not found")
    return path


def _manifest(project: Path) -> tuple[Path, dict]:
    path = project / "work" / "manifest.json"
    if not path.exists():
        raise HTTPException(409, "Project has no manifest. Run storyforge plan first.")
    return path, load_json(path)


def _scene(project: Path, scene_id: int) -> tuple[Path, dict, dict]:
    manifest_path, manifest = _manifest(project)
    for scene in manifest.get("scenes", []):
        if int(scene.get("id", -1)) == scene_id:
            return manifest_path, manifest, scene
    raise HTTPException(404, f"Scene {scene_id} not found")


def _safe_asset(project: Path, rel: str) -> Path:
    candidate = (project / rel).resolve()
    try:
        candidate.relative_to(project.resolve())
    except ValueError as exc:
        raise HTTPException(400, "Unsafe asset path") from exc
    return candidate


def _references(project: Path) -> dict:
    out = {"characters": [], "locations": [], "style": []}
    root = project / "references"
    for category in out:
        d = root / category
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                rel = p.relative_to(project).as_posix()
                if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    out[category].append({"path": rel, "url": f"/media/{project.name}/{rel}"})
                elif p.suffix.lower() in {".md", ".txt", ".json"}:
                    out[category].append({"path": rel, "url": None})
    return out


def _timeline_payload(project: Path) -> dict:
    _, manifest = _manifest(project)
    estimates = estimate_project(project)
    decisions = {int(d["scene_id"]): d for d in estimates.get("decisions", [])}
    scenes = []
    for scene in manifest.get("scenes", []):
        sid = int(scene["id"])
        item = dict(scene)
        item["decision"] = decisions.get(sid)
        key = scene.get("keyframe")
        gen = scene.get("generated_video")
        item["keyframe_exists"] = bool(key and _safe_asset(project, key).is_file())
        item["generated_exists"] = bool(gen and _safe_asset(project, gen).is_file())
        item["keyframe_url"] = f"/media/{project.name}/{key}" if item["keyframe_exists"] else None
        item["generated_url"] = f"/media/{project.name}/{gen}" if item["generated_exists"] else None
        item["image_state"] = scene.get("image_state") or ("CANDIDATE" if item["keyframe_exists"] else "NEEDS_IMAGE")
        packet = project / "work" / "image_packets" / f"scene_{sid:03}" / "image_prompt.md"
        item["image_prompt"] = packet.read_text(encoding="utf-8") if packet.exists() else ""
        prompt = project / "work" / "prompts" / f"scene_{sid:03}.txt"
        item["prompt"] = prompt.read_text(encoding="utf-8") if prompt.exists() else ""
        scenes.append(item)
    narration = manifest.get("narration")
    return {
        "project": project.name,
        "title": manifest.get("title", project.name),
        "duration": float(manifest.get("duration", 0.0)),
        "fps": int(manifest.get("fps", 30)),
        "resolution": manifest.get("resolution", [1920, 1080]),
        "narration_url": f"/media/{project.name}/{narration}" if narration and _safe_asset(project, narration).exists() else None,
        "budget": {k: v for k, v in estimates.items() if k != "decisions"},
        "routes": sorted(ROUTES),
        "image_states": sorted(IMAGE_STATES),
        "references": _references(project),
        "scenes": scenes,
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/projects")
def list_projects():
    result = []
    for p in sorted(_projects_root().iterdir()):
        if p.is_dir():
            result.append({"name": p.name, "has_manifest": (p / "work" / "manifest.json").exists()})
    return result


@app.get("/api/projects/{name}/timeline")
def get_timeline(name: str):
    return _timeline_payload(_project(name))


@app.get("/api/projects/{name}/inspect")
def inspect(name: str):
    return asdict(inspect_project(_project(name)))


@app.post("/api/projects/{name}/director")
def director(name: str):
    project = _project(name)
    path = write_director_plan(project)
    return {"plan_file": str(path), "estimate": estimate_project(project)}


@app.patch("/api/projects/{name}/scenes/{scene_id}")
def patch_scene(name: str, scene_id: int, patch: ScenePatch):
    project = _project(name)
    manifest_path, manifest, scene = _scene(project, scene_id)
    data = patch.model_dump(exclude_unset=True)
    if "route_override" in data:
        route = data["route_override"]
        if route in {None, "", "AUTO"}:
            scene.pop("route_override", None)
            data.pop("route_override", None)
        elif route not in ROUTES:
            raise HTTPException(400, f"Unknown route: {route}")
    if "image_state" in data:
        state = data["image_state"]
        if state not in IMAGE_STATES:
            raise HTTPException(400, f"Unknown image state: {state}")
    scene.update(data)
    save_json(manifest_path, manifest)
    return _timeline_payload(project)


@app.put("/api/projects/{name}/scenes/{scene_id}/prompt")
def save_prompt(name: str, scene_id: int, body: PromptPatch):
    project = _project(name)
    _scene(project, scene_id)
    out = project / "work" / "prompts" / f"scene_{scene_id:03}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body.prompt, encoding="utf-8")
    return {"ok": True, "path": str(out)}


@app.put("/api/projects/{name}/scenes/{scene_id}/image-prompt")
def save_image_prompt(name: str, scene_id: int, body: PromptPatch):
    project = _project(name)
    _scene(project, scene_id)
    packet = project / "work" / "image_packets" / f"scene_{scene_id:03}"
    packet.mkdir(parents=True, exist_ok=True)
    out = packet / "image_prompt.md"
    out.write_text(body.prompt, encoding="utf-8")
    set_image_state(project, scene_id, "BRIEF_READY")
    return {"ok": True, "path": str(out)}


@app.post("/api/projects/{name}/image-packets")
def image_packets(name: str):
    return create_image_packets(_project(name))


@app.post("/api/projects/{name}/scenes/{scene_id}/image-packet")
def image_packet(name: str, scene_id: int):
    return create_image_packets(_project(name), scene_ids={scene_id})


async def _save_upload(project: Path, scene_id: int, upload: UploadFile, kind: str) -> dict:
    manifest_path, manifest, scene = _scene(project, scene_id)
    suffix = Path(upload.filename or "").suffix.lower()
    content_type = (upload.content_type or "").lower()
    if kind == "keyframe":
        allowed = {".png", ".jpg", ".jpeg", ".webp"}
        if suffix not in allowed or (content_type and not content_type.startswith("image/")):
            raise HTTPException(415, "Keyframe must be PNG/JPEG/WebP")
        directory = project / "keyframes"
        filename = f"{scene_id:03}{suffix}"
        field = "keyframe"
        scene["image_state"] = "CANDIDATE"
    else:
        allowed = {".mp4", ".mov", ".mkv", ".webm"}
        if suffix not in allowed or (content_type and not content_type.startswith("video/") and suffix != ".mkv"):
            raise HTTPException(415, "Generated clip must be mp4/mov/mkv/webm")
        directory = project / "generated"
        filename = f"scene_{scene_id:03}{suffix}"
        field = "generated_video"
    directory.mkdir(parents=True, exist_ok=True)
    dst = directory / filename
    with dst.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    scene[field] = dst.relative_to(project).as_posix()
    save_json(manifest_path, manifest)
    return _timeline_payload(project)


@app.post("/api/projects/{name}/scenes/{scene_id}/keyframe")
async def upload_keyframe(name: str, scene_id: int, file: UploadFile = File(...)):
    return await _save_upload(_project(name), scene_id, file, "keyframe")


@app.post("/api/projects/{name}/scenes/{scene_id}/generated")
async def upload_generated(name: str, scene_id: int, file: UploadFile = File(...)):
    return await _save_upload(_project(name), scene_id, file, "generated")


@app.post("/api/projects/{name}/references/{category}")
async def upload_reference(name: str, category: str, reference_name: str = Form(...), file: UploadFile = File(...)):
    project = _project(name)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(415, "Reference image must be PNG/JPEG/WebP")
    temp = project / "work" / ("_reference_upload" + suffix)
    temp.parent.mkdir(parents=True, exist_ok=True)
    with temp.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        dst = save_reference(project, category, reference_name, temp)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        temp.unlink(missing_ok=True)
    return {"path": dst.relative_to(project).as_posix(), "references": _references(project)}


@app.post("/api/projects/{name}/scenes/{scene_id}/flow-packet")
def flow_packet(name: str, scene_id: int):
    return export_flow_packets(_project(name), scene_ids={scene_id})


@app.post("/api/projects/{name}/render")
def render_project(name: str):
    project = _project(name)
    inspection = inspect_project(project)
    if not inspection.valid:
        raise HTTPException(409, {"errors": inspection.errors})
    output = render(project)
    return {"output": str(output)}


@app.get("/media/{name}/{asset_path:path}")
def media(name: str, asset_path: str):
    project = _project(name)
    path = _safe_asset(project, asset_path)
    if not path.is_file():
        raise HTTPException(404, "Asset not found")
    return FileResponse(path, media_type=mimetypes.guess_type(path.name)[0])


def main(host: str = "127.0.0.1", port: int = 8766, open_browser: bool = True):
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Install Studio support with: pip install -e '.[studio]'") from exc
    url = f"http://{host}:{port}"
    print(f"StoryForge Studio: {url}")
    if open_browser:
        webbrowser.open(url)
    uvicorn.run("storyforge.studio:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
