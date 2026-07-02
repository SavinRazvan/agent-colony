# Upgrade MAS Workflow Kit

Re-run install from a **newer kit source** (git tag, plugin payload, or local clone) into the same consumer project.

## Before upgrade

1. Note current version: `cat .ai_infra/.kit-version`
2. Commit or stash local changes (especially `.cursor/`, `.ai_infra/`, `.local/`)
3. Back up custom overlays under `overlays/rules/` and any `mcp.user.json` secrets

## Upgrade command

**Light refresh (dashboards + activate scripts, keeps trackers):**

```bash
cd ~/Projects/my-app    # your activated project
source .venv/bin/activate
python3 -m cursor_workflow activate --directory .
```

Same as **`/workflow-activate`** in Agent chat when planes are already ready. Refreshes kit-managed dashboard HTML, `pages.json`, and install scripts from the plugin payload.

**Full reinstall (scripts, agents, rules — review `.local/` merge):**

```bash
python3 -m cursor_workflow activate --directory . --force
```

**Kit clone / advanced** — from kit repo:

```bash
export TARGET=~/Projects/my-app
.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" \
  --source . \
  --profile with_mcp \
  --with-mcp-json \
  --verify
```

Use `--source payload` when running from the distribution root (see `workflow-activate` skill).

## What install updates

| Area | Behavior |
|------|----------|
| `.ai_infra/scripts/` | Overwritten from manifest profile |
| `.cursor/agents`, rules, skills | Overwritten from kit |
| `.local/` exemplars | Re-copied on **`--force`** only; light re-activate refreshes dashboards + `pages.json` |
| Dashboard HTML / `pages.json` | Refreshed on every `activate` (idempotent) |
| `AGENTS.md` | **Not** overwritten if present — delete to refresh from stub, or merge manually |
| `mcp.user.json` | **Not** overwritten — merge via `python3 -m cursor_workflow mcp validate` |
| `.kit-version` | Updated to manifest `kit_version` |

## After upgrade

```bash
cd ~/Projects/my-app
python3 -m cursor_workflow gates
python3 -m cursor_workflow health
python3 -m cursor_workflow mcp validate
```

## Rollback

1. Restore project from git to pre-upgrade commit
2. Or reinstall from previous kit tag/payload matching old `.kit-version`

Document intentional divergences in `.local/index-and-planning/current/updates-log.md`.
