# Upgrade MAS Workflow Kit

Re-run install from a **newer kit source** (git tag, plugin payload, or local clone) into the same consumer project.

## Before upgrade

1. Note current version: `cat .ai_infra/.kit-version`
2. Commit or stash local changes (especially `.cursor/`, `.ai_infra/`, `.local/`)
3. Back up custom overlays under `overlays/rules/` and any `mcp.user.json` secrets

## Upgrade command

From kit / payload root:

```bash
cursor-workflow install \
  --target /path/to/your-project \
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
| `.local/` exemplars | Re-copied; **review** `plan.md` / `work-tracker.md` for merge |
| `mcp.user.json` | **Not** overwritten — merge via `cursor-workflow mcp validate` |
| `.kit-version` | Updated to manifest `kit_version` |

## After upgrade

```bash
cursor-workflow gates --directory /path/to/your-project
cursor-workflow health --directory /path/to/your-project
cursor-workflow mcp validate
```

## Rollback

1. Restore project from git to pre-upgrade commit
2. Or reinstall from previous kit tag/payload matching old `.kit-version`

Document intentional divergences in `.local/index-and-planning/current/updates-log.md`.
