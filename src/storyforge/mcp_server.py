"""MCP façade for StoryForge."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from .config import Settings, masked_provider_status
from .planner import plan
from .prompts import export_prompts
from .render import render
from .generate import generate_project
from .director import inspect_project, estimate_project, write_director_plan
from .flow_export import export_flow_packets
from .image_packets import create_image_packets, set_image_state

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Install MCP support with: pip install -e '.[mcp]'") from exc

mcp = FastMCP("NarrateAnimateAwesomeGreat")


def project_path(name: str) -> Path:
    settings = Settings.from_env()
    safe = Path(name).name
    if safe != name or safe in {"", ".", ".."}:
        raise ValueError("Invalid project name")
    root = settings.projects_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = (root / safe).resolve()
    if path.parent != root:
        raise ValueError("Project path escapes configured projects directory")
    return path


@mcp.tool()
def provider_status() -> dict[str, bool]:
    return masked_provider_status()


@mcp.tool()
def list_projects() -> list[str]:
    root = Settings.from_env().projects_dir.resolve()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


@mcp.tool()
def create_project(name: str) -> str:
    p = project_path(name)
    for d in ["keyframes", "generated", "music", "sfx", "work", "work/reviews", "output", "references/characters", "references/locations", "references/style"]:
        (p / d).mkdir(parents=True, exist_ok=True)
    story = p / "story.txt"
    if not story.exists():
        story.write_text("Paste your story here.\n", encoding="utf-8")
    return str(p)


@mcp.tool()
def inspect_story_project(name: str) -> dict:
    return asdict(inspect_project(project_path(name)))


@mcp.tool()
def plan_project(name: str, whisper: bool = False) -> dict:
    m = plan(project_path(name), whisper)
    return {"title": m["title"], "duration": m["duration"], "scenes": len(m["scenes"]), "alignment": m.get("alignment")}


@mcp.tool()
def build_image_generation_packets(name: str, scene_ids: list[int] | None = None, overwrite: bool = False) -> dict:
    """Create ChatGPT/Gemini-ready initial-image briefs with neighboring context and reference inventory."""
    return create_image_packets(project_path(name), set(scene_ids or []) or None, overwrite=overwrite)


@mcp.tool()
def mark_scene_image_state(name: str, scene_id: int, state: str) -> dict:
    """Mark an initial scene image as BRIEF_READY, CANDIDATE, APPROVED, REJECTED, or NEEDS_IMAGE."""
    return set_image_state(project_path(name), scene_id, state)


@mcp.tool()
def build_director_plan(name: str, prefer_local: bool = True) -> dict:
    p = project_path(name)
    out = write_director_plan(p, prefer_local=prefer_local)
    result = estimate_project(p, prefer_local=prefer_local)
    result["plan_file"] = str(out)
    return result


@mcp.tool()
def estimate_generation_cost(name: str, prefer_local: bool = True) -> dict:
    return estimate_project(project_path(name), prefer_local=prefer_local)


@mcp.tool()
def export_generation_prompts(name: str) -> str:
    p = project_path(name)
    export_prompts(p)
    return str(p / "work" / "generation_queue.csv")


@mcp.tool()
def export_flow_subscription_packets(name: str, scene_ids: list[int] | None = None) -> dict:
    return export_flow_packets(project_path(name), scene_ids=set(scene_ids or []) or None)


@mcp.tool()
def generate_scenes(name: str, provider: str = "flow", scene_ids: list[int] | None = None, dry_run: bool = True) -> list[dict]:
    return generate_project(project_path(name), provider, set(scene_ids or []) or None, dry_run=dry_run)


@mcp.tool()
def render_project(name: str, captions: bool = True) -> str:
    project = project_path(name)
    inspection = inspect_project(project)
    if not inspection.valid:
        raise RuntimeError("Project validation failed: " + "; ".join(inspection.errors))
    return str(render(project, captions=captions))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
