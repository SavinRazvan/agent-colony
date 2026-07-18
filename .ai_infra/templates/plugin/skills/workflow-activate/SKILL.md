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

Re-activate does not overwrite trackers, `user_settings/`, or `AGENTS.md`. Kit-managed dashboard HTML, JS/CSS, `module-audit.html`, and `pages.json` refresh from the activate source (`payload/` when resolved) or embedded `.ai_infra/templates/local-workspace/`.

- Idempotent: skips full install when all planes already pass `install-contract.json`, but still refreshes dashboards
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

**MCP config files:** the Marketplace repo-root `agents/`, `rules/`, `skills/` trees load agents,
skills, and rules only. MCP examples install under `.cursor/` from **payload** when `activate`
runs — not before. Use **`/connect-external-mcp`** after activate.

## Post-activate (user focus — not automated)

1. Edit `.local/user_settings/github.collaboration.yaml` (owner, pipelines, provenance)
2. Optional: `.local/user_settings/mcp.agents.yaml`
3. `python -m cursor_workflow contributors validate`
4. `python -m cursor_workflow integrate validate`

## Adding agents/skills/MCP later

Invoke subagent **`/integrator-mas-agent`** with skill **`/mas-infrastructure-integration`** — not shell commands.

## Agent delegation

After plugin enable, parent agent or user should:

0. If plugin not installed: Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` (chat only — not terminal). Show [install screenshot](https://raw.githubusercontent.com/SavinRazvan/mas-workflow-kit-project-ssot/main/assets/mas-workflow-kit-install.png) — user clicks the **MAS Workflow Kit** card in the preview.
1. Run **`workflow_activate`** or `cursor_workflow activate`
2. Hand user to personalize `user_settings/`
3. Optionally delegate **`/integrator-mas-agent`** for extensions

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- `integrate validate` exit 0

## Reference

- [PLUGIN-USER-GUIDE.md](../../../docs/operations/PLUGIN-USER-GUIDE.md) — unified consumer manual
- [ADR-001 Option B](../../../docs/decisions/ADR-001-distribution-activation.md)
- [consumer-quickstart.md](../../../docs/operations/consumer-quickstart.md)
