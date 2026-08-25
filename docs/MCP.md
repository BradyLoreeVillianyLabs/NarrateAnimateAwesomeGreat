# StoryForge MCP server

The MCP server lets an MCP-capable assistant or IDE operate the movie pipeline through project-level tools instead of shell commands.

## Install

```bash
pip install -e '.[mcp]'
```

For everything:

```bash
pip install -e '.[all]'
```

## Start locally

```bash
storyforge-mcp
```

The default is **stdio**, which is the safest/easiest transport for a local MCP host because it does not expose a network port.

## Tools exposed

- `provider_status` — tells the agent which providers are configured, never their keys
- `list_projects`
- `create_project`
- `plan_project`
- `export_generation_prompts`
- `generate_scenes`
- `render_project`

`generate_scenes` defaults to `dry_run=true`. This is deliberate: connecting an agent must not start spending cloud video credits merely by inspecting a project.

## Example MCP host configuration

The exact outer configuration format depends on the host. A typical local stdio entry looks like:

```json
{
  "mcpServers": {
    "storyforge": {
      "command": "storyforge-mcp",
      "env": {
        "STORYFORGE_PROJECTS_DIR": "C:/path/to/NarrateAnimateAwesomeGreat/projects"
      }
    }
  }
}
```

Do **not** paste cloud keys into a checked-in MCP JSON file. Put them in the repository's local `.env`, OS environment, or the MCP host's secure secret facility.

## Security boundaries

MCP accepts a **project name**, not an arbitrary filesystem path. This prevents a connected model from using StoryForge tools as a general-purpose filesystem interface.

Provider status returns booleans only. Secrets are never returned.

Rendering can execute FFmpeg against assets inside a project. Treat MCP clients with the same trust you would give a local automation program.

## Remote MCP

The current entry point intentionally starts stdio. The MCP Python SDK also supports Streamable HTTP. If remote access is added, require authentication and TLS at the deployment boundary; do not simply bind the development server to the public internet.
