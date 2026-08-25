# VS Code: Codex + Claude + StoryForge

This repository is designed to use two coding agents with deliberately different responsibilities.

## Codex: builder/integrator

Codex should read `AGENTS.md` before making changes. Its default role is implementation, integration, testing and deterministic production work.

Good Codex tasks:

```text
Read AGENTS.md and inspect the repository.
Validate project my-film, build its director plan, and identify the smallest implementation work required for the next production milestone. Do not trigger paid generation. Run relevant tests after code changes.
```

## Claude: adversarial reviewer

Claude should read `CLAUDE.md`. Its role is to challenge scene plans, prompts, continuity, unnecessary cloud spend and code regressions.

Good Claude task:

```text
Read CLAUDE.md. Review projects/my-film/work/manifest.json and director_plan.json. Find continuity, pacing, generation-risk and unnecessary-cost problems. Do not trigger paid generation. Put actionable findings in projects/my-film/work/reviews/claude-review.md.
```

## Shared MCP server

Install MCP support:

```bash
pip install -e '.[mcp]'
```

Start the server over stdio:

```bash
storyforge-mcp
```

The MCP surface exposes project-scoped tools for:
- listing/creating projects;
- validation/inspection;
- narration planning;
- director routing;
- cost estimation;
- prompt export;
- dry-run generation;
- final rendering.

Configure your VS Code agent/MCP host to launch the `storyforge-mcp` executable from this repository's virtual environment. Exact MCP configuration UI/file names can change between extension versions, so prefer the extension's current MCP configuration interface rather than copying stale editor-specific JSON from the internet.

## Recommended collaboration loop

```text
1. USER supplies story + narration + keyframes
2. Codex validates and builds director plan
3. Claude reviews plan/continuity/cost
4. Codex verifies findings and applies justified fixes
5. StoryForge exports generation packets
6. USER uses subscription UI and/or approves API generation
7. Generated clips land in generated/scene_###.mp4
8. Codex validates assets and renders preview
9. Claude reviews preview findings
10. StoryForge renders/upscales final master
```

## Cost approval

`estimate_generation_cost` and `storyforge cost` do not spend money.

The configured budget is in `.env`:

```dotenv
STORYFORGE_MAX_PROJECT_GENERATION_USD=20.00
```

Treat the estimator as planning data; actual provider billing can differ. Update configured per-second rates when provider pricing changes.

## Subscription-assisted mode

ChatGPT/Codex, Claude and Gemini subscription interfaces remain useful even without API keys. StoryForge can export prompts/assets, and returned video files can simply be placed in `generated/`.

Do not browser-automate consumer subscription interfaces to imitate an API. Use their supported UI/IDE workflows or separately configured APIs.
