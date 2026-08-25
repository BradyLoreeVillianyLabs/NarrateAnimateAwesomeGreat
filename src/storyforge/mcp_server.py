"""MCP façade for StoryForge.

Run locally with `storyforge-mcp`. The server exposes safe project-level tools;
it never returns environment secrets.
"""
from __future__ import annotations

from pathlib import Path
from .config import Settings, masked_provider_status
from .planner import plan
from .prompts import export_prompts
from .render import render
from .generate import generate_project

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Install MCP support with: pip install -e '.[mcp]'") from exc

mcp = FastMCP("NarrateAnimateAwesomeGreat")


def project_path(name: str) -> Path:
    settings = Settings.from_env()
    # Project names, not arbitrary paths, are accepted over MCP.
    safe = Path(name).name
    if safe != name or safe in {"", ".", ".."}:
        raise ValueError("Invalid project name")
    return settings.projects_dir / safe


@mcp.tool()
def provider_status() -> dict[str, bool]:
    """Report which video providers are configured without exposing credentials."""
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
    """Create a new empty story project and its standard folders."""
    p = project_path(name)
    for d in ["keyframes", "generated", "music", "sfx", "work", "output"]:
        (p / d).mkdir(parents=True, exist_ok=True)
    story = p / "story.txt"
    if not story.exists():
        story.write_text("Paste your story here.\n", encoding="utf-8")
    return str(p)


@mcp.tool()
def plan_project(name: str, whisper: bool = False) -> dict:
    """Align story/narration and create the canonical scene manifest."""
    m = plan(project_path(name), whisper)
    return {"title": m["title"], "duration": m["duration"], "scenes": len(m["scenes"])}


@mcp.tool()
def export_generation_prompts(name: str) -> str:
    """Create image-to-video prompts and generation_queue.csv for a project."""
    p = project_path(name)
    export_prompts(p)
    return str(p / "work" / "generation_queue.csv")


@mcp.tool()
def generate_scenes(name: str, provider: str = "manual", scene_ids: list[int] | None = None, dry_run: bool = True) -> list[dict]:
    """Generate selected scenes. Defaults to dry-run to prevent accidental API spend."""
    return generate_project(project_path(name), provider, set(scene_ids or []) or None, dry_run=dry_run)


@mcp.tool()
def render_project(name: str, captions: bool = True) -> str:
    """Render a project's current assets into its YouTube master."""
    return str(render(project_path(name), captions=captions))


def main():
    # FastMCP defaults to local stdio, ideal for Claude Desktop/Codex/IDE hosts.
    # Transport can be extended to Streamable HTTP without changing tool functions.
    mcp.run()


if __name__ == "__main__":
    main()
