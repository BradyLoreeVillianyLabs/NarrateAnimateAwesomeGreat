"""MCP façade for StoryForge.

Run locally with `storyforge-mcp`. The server exposes safe project-level tools;
it never returns environment secrets. Billable generation defaults to dry-run.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from .config import Settings, masked_provider_status
from .planner import plan
from .prompts import export_prompts
from .render import render
from .generate import generate_project
from .director import inspect_project, estimate_project, write_director_plan

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
    return settings.projects_dir / safe


@mcp.tool()
def provider_status() -> dict[str, bool]:
    """Report configured video providers without exposing credentials."""
    return masked_provider_status()


@mcp.tool()
def list_projects() -> list[str]:
    """List StoryForge projects."""
    root = Settings.from_env().projects_dir
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


@mcp.tool()
def create_project(name: str) -> str:
    """Create an empty story project and standard folders."""
    p = project_path(name)
    for d in ["keyframes", "generated", "music", "sfx", "work", "work/reviews", "output"]:
        (p / d).mkdir(parents=True, exist_ok=True)
    story = p / "story.txt"
    if not story.exists():
        story.write_text("Paste your story here.\n", encoding="utf-8")
    return str(p)


@mcp.tool()
def inspect_story_project(name: str) -> dict:
    """Validate project structure/timeline/assets and report warnings without changing files."""
    return asdict(inspect_project(project_path(name)))


@mcp.tool()
def plan_project(name: str, whisper: bool = False) -> dict:
    """Align story/narration and create the canonical scene manifest."""
    m = plan(project_path(name), whisper)
    return {"title": m["title"], "duration": m["duration"], "scenes": len(m["scenes"])}


@mcp.tool()
def build_director_plan(name: str, prefer_local: bool = True) -> dict:
    """Route every scene to still/local/cheap-cloud/hero-cloud and estimate spend."""
    p = project_path(name)
    out = write_director_plan(p, prefer_local=prefer_local)
    result = estimate_project(p, prefer_local=prefer_local)
    result["plan_file"] = str(out)
    return result


@mcp.tool()
def estimate_generation_cost(name: str, prefer_local: bool = True) -> dict:
    """Estimate generation cost using configured rates. Does not call any provider."""
    return estimate_project(project_path(name), prefer_local=prefer_local)


@mcp.tool()
def export_generation_prompts(name: str) -> str:
    """Create I2V prompts and generation_queue.csv for a project."""
    p = project_path(name)
    export_prompts(p)
    return str(p / "work" / "generation_queue.csv")


@mcp.tool()
def generate_scenes(name: str, provider: str = "manual", scene_ids: list[int] | None = None, dry_run: bool = True) -> list[dict]:
    """Generate selected scenes. Defaults to dry-run to prevent accidental API spend."""
    return generate_project(project_path(name), provider, set(scene_ids or []) or None, dry_run=dry_run)


@mcp.tool()
def render_project(name: str, captions: bool = True) -> str:
    """Render current assets into a YouTube master."""
    inspection = inspect_project(project_path(name))
    if not inspection.valid:
        raise RuntimeError("Project validation failed: " + "; ".join(inspection.errors))
    return str(render(project_path(name), captions=captions))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
