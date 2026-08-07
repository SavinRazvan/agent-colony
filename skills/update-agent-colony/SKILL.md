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

## When

User already ran **`/workflow-activate`** in **their app**, then updated the **Agent Colony** plugin (or kit tag) and needs kit-managed files refreshed.

**Not for first install** — use [workflow-activate](workflow-activate/SKILL.md) when `.ai_infra/` is missing.

## Guide the user

1. Confirm the open folder is **their activated app**, not the kit product repo.
2. Prefer Agent chat **`/update-agent-colony`**, or the Pattern A command below.
3. Explain version gate briefly:
   - **same / newer installed** → light heal (dashboards, `.gitignore`, `STARTER-001`, missing `.venv`)
   - **source newer** or **`--force`** → full overwrite of kit-managed agents/rules/skills/scripts
4. After upgrade: `health` + `mcp validate`.

## One command

```bash
source .venv/bin/activate
python3 -m agent_colony update --directory .
```

**Check only (no writes):**

```bash
python3 -m agent_colony update --directory . --check
```

**Force full refresh** (even when versions match):

```bash
python3 -m agent_colony update --directory . --force
```

**Source resolution** matches activate: `WORKFLOW_KIT_PAYLOAD` → `./payload/` → kit/plugin `payload/` → `--source`.

## What update does

| Condition | Action |
|-----------|--------|
| No `.ai_infra/` or missing `.kit-version` | Fail — tell user to run `/workflow-activate` |
| `installed == available` (and not `--force`) | Light heal only |
| `available > installed` or `--force` | Full scaffold refresh (same as `activate --force`) |

**Preserved:** `AGENTS.md` (if present), `mcp.user.json`, `.local/user_settings/`, existing trackers.

**Overwritten on upgrade:** `.cursor/agents|rules|skills`, `.ai_infra/scripts`, `agent_colony/` CLI copy, `.kit-version`, kit-managed dashboards.

## Post-update

```bash
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```

Optional: `integrate validate`, `canvas doctor`. Breaking renames: [upgrade-kit.md](../../.ai_infra/docs/operations/upgrade-kit.md).

## Anti-patterns

- Do not tell users to re-run plain `/workflow-activate` expecting agents/skills to refresh — that path only heals when planes are ready.
- Do not overwrite consumer `user_settings` or invent a second Status writer under `board_only`.
- Do not run update against the kit-dev repo as a self-upgrade without an explicit external `--source`.
