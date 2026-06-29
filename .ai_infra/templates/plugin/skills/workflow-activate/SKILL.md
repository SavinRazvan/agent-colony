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
| Runtime | `.local/` trackers + `user_settings/` exemplars | No — gitignored |

- Idempotent: skips install when all planes already pass `install-contract.json`
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

## Post-activate (user focus — not automated)

1. Edit `.local/user_settings/github.collaboration.yaml` (owner, pipelines, provenance)
2. Optional: `.local/user_settings/mcp.agents.yaml`
3. `python -m cursor_workflow contributors validate`
4. `python -m cursor_workflow integrate validate`

## Adding agents/skills/MCP later

Invoke Cursor agent **`integrator-mas-agent`** (chat / @ picker — **not** a shell command) with skill **`mas-infrastructure-integration`**.

## Agent delegation

After plugin enable, parent agent or user should:

1. Run **`workflow_activate`** or `cursor_workflow activate`
2. Hand user to personalize `user_settings/`
3. Optionally delegate **`integrator-mas-agent`** for extensions

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- `integrate validate` exit 0

## Reference

- ADR-001 Option B · `PLUGIN-ARCHITECTURE.md` § Automated activation
- `consumer-quickstart.md`
