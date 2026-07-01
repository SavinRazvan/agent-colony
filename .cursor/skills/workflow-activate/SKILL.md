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
---
name: workflow-activate
description: Install MAS Workflow Kit infrastructure into the current workspace from the plugin payload (ADR-001 Option B).
---

# Workflow activate

## When

First use after enabling the **MAS Workflow Kit** plugin in a project workspace — or when any of the three planes is missing on disk.

## One command (agent or human)

From the **open workspace** (Pattern A — one script command):

```bash
python -m cursor_workflow activate --directory .
```

**Auto source resolution:** `WORKFLOW_KIT_PAYLOAD` env → `./payload/` → kit `payload/` (plugin bundle). Override with `--source /path/to/payload`.

**MCP:** `workflow_activate` on the `workflow-kit` server (same behavior).

## What `activate` does

| Plane | Paths installed | Cursor loads? |
|-------|-----------------|---------------|
| Cursor contract | `.cursor/`, `.agents/`, `AGENTS.md` | Yes |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` | No — scripts/CLI |
| Runtime | `.local/` Tier 1 scaffold: trackers, six `workflow-artifacts/*` buckets + README stubs, `pages.json`, dashboards; `user_settings/` exemplars | No — gitignored |

Tier 1 paths are created on first install; Tier 2 runtime `.md` files appear when agents/scripts run. See [local-workspace-layout.md](../../.ai_infra/docs/operations/local-workspace-layout.md) § Artifact tiers. Re-activate does not overwrite existing trackers, `AGENTS.md`, or `pages.json`.

- Idempotent: skips install when all planes already pass `install-contract.json`
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

**MCP config files:** The Marketplace `plugin/` tree loads agents, skills, and rules only. MCP examples (`mcp.json.kit.example`, `mcp.registry.yaml.example`, `mcp.user.example.json`, `MCP-CONFIG.md`) install under `.cursor/` from **payload** when `activate` runs — not before. Use skill **`connect-external-mcp`** after activate.

## Post-activate (user focus — not automated)

1. Edit `.local/user_settings/github.collaboration.yaml` (owner, pipelines, provenance)
2. Optional: `.local/user_settings/mcp.agents.yaml`
3. `python -m cursor_workflow contributors validate`
4. `python -m cursor_workflow integrate validate`

## Adding agents/skills/MCP later

Invoke Cursor agent **`integrator-mas-agent`** (chat / @ picker — **not** a shell command) with skill **`mas-infrastructure-integration`**.

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- `integrate validate` exit 0

## Reference

- ADR-001 Option B · `PLUGIN-ARCHITECTURE.md` § Automated activation
- `consumer-quickstart.md`
