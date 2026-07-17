<!--
File: README.md
Path: .ai_infra/templates/user-settings/README.md
Role: Maintainer docs for user-settings exemplars copied into `.local/user_settings/` at install.
Used By:
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/docs/operations/local-workspace-layout.md
Depends On:
 - exemplars/github.collaboration.yaml
 - exemplars/mcp.agents.yaml
Notes:
 - `.local/user_settings/` is gitignored; these exemplars are the versioned source.
-->

# User settings templates

**Purpose:** One-time (or occasional) YAML worksheets under **`.local/user_settings/`** so humans configure GitHub collaboration and MCP agent wiring without editing kit scripts.

| Exemplar | Copied to | Feeds |
|----------|-----------|--------|
| `exemplars/github.collaboration.yaml` | `.local/user_settings/github.collaboration.yaml` | Commit trailers, PR bodies, PR phase artifacts |
| `exemplars/mcp.agents.yaml` | `.local/user_settings/mcp.agents.yaml` | `.cursor/mcp.user.json`, `.cursor/mcp.registry.yaml` |

**Agents:** Read completed files for attribution defaults and MCP intent. Wired integration:

- PR scripts: `review.py`, `prepare.py`, `merge.py` — `--pipeline default` reads owner + agents from YAML
- CLI: `python -m cursor_workflow contributors {validate|show|commit-trailers|pr-body}`
- MCP: `workflow_render_commit_trailers`, `workflow_render_pr_body`, `workflow_contributors_validate`

**Examples:** [RENDERED-EXAMPLES.md](RENDERED-EXAMPLES.md) — kit vs legacy commit/PR formats.

**Do not commit** `.local/user_settings/` — see [local-workspace-layout.md](../../docs/operations/local-workspace-layout.md).
