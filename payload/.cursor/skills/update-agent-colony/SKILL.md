---
name: update-agent-colony
description: Upgrade an already-activated consumer workspace to the latest kit payload (version-gated heal vs full refresh).
---
<!--
File: SKILL.md
Path: .cursor/skills/update-agent-colony/SKILL.md
Role: Consumer-facing kit upgrade after Marketplace/plugin bump (ADR-001 Option B follow-on).
Used By:
 - PLUGIN-USER-GUIDE.md
 - upgrade-kit.md
 - sync_plugin_bundle.py (canonical; template fallback at .ai_infra/templates/plugin/skills/)
Depends On:
 - .ai_infra/install/agent_colony/update_cli.py
 - .cursor/skills/workflow-activate/SKILL.md (first install only)
Notes:
 - Pattern A: one script command per action. First install remains /workflow-activate.
-->

# Update Agent Colony

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

User ran **`/workflow-activate`** in **their app**, then updated the Agent Colony plugin and needs kit-managed files refreshed.

**Not for first install** — use [workflow-activate](workflow-activate/SKILL.md) when `.ai_infra/` is missing.

## Guide the user

1. Confirm folder is **their activated app**, not kit-dev repo.
2. Prefer **`/update-agent-colony`** or Pattern A command below.
3. Version gate:
   - **same / newer installed** → light heal (dashboards, `.gitignore`, `STARTER-001`, missing `.venv`)
   - **source newer** or **`--force`** → full overwrite of kit-managed agents/rules/skills/scripts
4. After upgrade: `health` + `mcp validate`.

## Commands

```bash
source .venv/bin/activate
python3 -m agent_colony update --directory .
python3 -m agent_colony update --directory . --check      # no writes; reports kit agent deltas vs payload
python3 -m agent_colony update --directory . --force      # full refresh (run --check first)
```

**Source resolution:** `WORKFLOW_KIT_PAYLOAD` → `./payload/` → kit/plugin `payload/` → `--source`.

## What update does

| Condition | Action |
|-----------|--------|
| No `.ai_infra/` or missing `.kit-version` | Fail — run `/workflow-activate` |
| `installed == available` (not `--force`) | Light heal only |
| `available > installed` or `--force` | Full scaffold refresh |

**`update --check`:** prints planned action plus diffs on the eight kit agent files vs payload. Exit **1** when local kit agent edits would be lost on upgrade/`--force`. Integrator **extra** agents print as warnings only.

**Preserved:** `AGENTS.md` (if present), `mcp.user.json`, `.local/user_settings/`, trackers.

**Overwritten on upgrade:** `.cursor/agents|rules|skills`, `.ai_infra/scripts`, `agent_colony/` CLI, `.kit-version`, dashboards.

## Post-update

```bash
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```

Optional: `integrate validate`, `canvas doctor`. Breaking renames: [upgrade-kit.md](../../.ai_infra/docs/operations/upgrade-kit.md).

## Anti-patterns

- Re-run plain `/workflow-activate` expecting agents/skills refresh — heals only when planes ready.
- Overwrite consumer `user_settings` or invent second Status writer under `board_only`.
- Run `update --force` in **kit-dev repo** — fails (`forbidden in slim install`). Kit-dev: edit sources → `make sync-plugin` → commit.
