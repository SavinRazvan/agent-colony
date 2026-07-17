---
name: workflow-activate
description: Install MAS Workflow Kit infrastructure into the current workspace from the plugin payload (ADR-001 Option B).
---
<!--
File: SKILL.md
Path: .cursor/skills/workflow-activate/SKILL.md
Role: Install MAS Workflow Kit three planes into the open workspace (ADR-001 Option B).
Used By:
 - PLUGIN-ARCHITECTURE.md
 - sync_plugin_bundle.py (canonical; template fallback at .ai_infra/templates/plugin/skills/)
Depends On:
 - .ai_infra/install/cursor_workflow/activate_cli.py
Notes:
 - Pattern A: one script command per action.
-->

# Workflow activate

## When

User enabled the **MAS Workflow Kit** plugin and opened **their project** (not the kit repo). Run on first use or when planes are missing.

## Guide the user (keep it simple)

1. If plugin not installed: Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit` (chat only — not terminal). Show [install screenshot](https://raw.githubusercontent.com/SavinRazvan/mas-workflow-kit/main/assets/mas-workflow-kit-install.png) or [consumer-quickstart § step 1](../../.ai_infra/docs/operations/consumer-quickstart.md#step-1-detail--install-plugin-from-github) — user clicks the **MAS Workflow Kit** card in the preview.
2. Confirm the open folder is **their app**, not `mas-workflow-kit`.
3. Run activate (below) — or tell them to pick **`/workflow-activate`** from the **`/`** menu.
4. Tell them to edit `.local/user_settings/github.collaboration.yaml` → `contributors validate`.
5. Point them to **`/implementer`** (from **`/`** menu) and `session-pointer.md`.

Do **not** dump gate lists or maintainer `make` commands.

## One command

From the **open workspace** (Pattern A — one script command):

```bash
python3 -m cursor_workflow activate --directory .
```

**Auto source resolution:** `WORKFLOW_KIT_PAYLOAD` env → `./payload/` → kit `payload/` (plugin bundle). Override with `--source /path/to/payload`.

**MCP:** `workflow_activate` on the `workflow-kit` server (same behavior).

## What `activate` does

| Plane | Paths installed | Cursor loads? |
|-------|-----------------|---------------|
| Cursor contract | `.cursor/`, `.agents/`, `AGENTS.md` | Yes |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` | No — scripts/CLI |
| Runtime | `.local/` Tier 1 scaffold: trackers, six `workflow-artifacts/*` buckets + README stubs, `pages.json`, dashboards; `user_settings/` exemplars | No — gitignored |

Tier 1 paths are created on first install; Tier 2 runtime `.md` files appear when agents/scripts run. See [local-workspace-layout.md](../../.ai_infra/docs/operations/local-workspace-layout.md) § Artifact tiers. Re-activate does not overwrite existing trackers, `user_settings/`, or `AGENTS.md`. Kit-managed dashboard HTML, JS/CSS assets, `module-audit.html`, and `pages.json` are refreshed from the activate source (plugin `payload/` when resolved) or embedded `.ai_infra/templates/local-workspace/` when not.

- Idempotent: skips full install when all planes already pass `install-contract.json`, but still refreshes dashboards
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

**MCP config files:** The Marketplace repo-root `agents/`, `rules/`, `skills/` trees load agents, skills, and rules only. MCP examples (`mcp.json.kit.example`, `mcp.registry.yaml.example`, `mcp.user.example.json`, `MCP-CONFIG.md`) install under `.cursor/` from **payload** when `activate` runs — not before. Use **`/connect-external-mcp`** after activate.

## Post-activate (tell the user)

1. Open `.local/user_settings/github.collaboration.yaml` — set **display_name** and **github_user**
2. Terminal: `source .venv/bin/activate && python3 -m cursor_workflow contributors validate` (must PASS before git/PR)
3. **`/implementer`** to start · read `session-pointer.md` first each session

**Dashboards (optional):** from project root run `python3 -m http.server 8000`, then open
http://localhost:8000/.local/agents-control-center/dashboards/index.html (not `file://`).

Optional: `integrate validate`, `health`. Add infrastructure later: **`/integrator-mas-agent`**.

## Adding agents/skills/MCP later

Invoke subagent **`/integrator-mas-agent`** with skill **`/mas-infrastructure-integration`** — not shell commands ([Subagents](https://cursor.com/docs/subagents), [Skills](https://cursor.com/docs/skills)).

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- `integrate validate` exit 0

## Reference

- [PLUGIN-USER-GUIDE.md](../../.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) — unified consumer manual
- [ADR-001 Option B](../../.ai_infra/docs/decisions/ADR-001-distribution-activation.md)
- [consumer-quickstart.md](../../.ai_infra/docs/operations/consumer-quickstart.md)
