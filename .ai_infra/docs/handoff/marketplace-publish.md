<!--
File: marketplace-publish.md
Path: .ai_infra/docs/handoff/marketplace-publish.md
Role: Checklist for building and publishing the MAS Workflow Kit Cursor plugin.
Used By:
 - REFACTOR-006
Depends On:
 - .ai_infra/scripts/release/sync_plugin_bundle.py
 - .cursor-plugin/plugin.json
Notes:
 - ADR-001 Option B: payload + workflow-activate skill.
-->

# Marketplace publish checklist

**Product:** MAS Workflow Kit · **Plugin id:** `mas-workflow-kit`

## Pre-publish (kit repo)

1. `make gates` — kit repo green
2. `make install-dry-run` — consumer install green
3. `make sync-plugin` — rebuild `plugin/` + `payload/`
4. `make check-plugin` — bundle parity green
5. `python .ai_infra/scripts/architecture/check_debrand.py`
6. Bump `version` in `.cursor-plugin/plugin.json` and `cursor_workflow.__version__` together

## Bundle layout

```text
.cursor-plugin/plugin.json
plugin/          # Cursor-loaded agents, skills, rules
payload/         # ADR-001 install source (.ai_infra + cursor_workflow shim)
```

## Local smoke (`/add-plugin` from repo path)

1. Run `make sync-plugin`
2. In Cursor: add plugin from kit repo root (must contain `.cursor-plugin/plugin.json`)
3. Confirm agents load: `implementer`, `enterprise-auditor`, maintainer slash skills
4. Run **workflow-activate** skill command:

```bash
python payload/cursor_workflow install \
  --target /path/to/project \
  --source payload \
  --profile with_mcp \
  --with-venv \
  --verify
```

5. In target: `python payload/cursor_workflow gates --directory /path/to/project` (or installed `cursor_workflow` if on PATH)

## Publish

- Document target channel (Cursor Marketplace vs local `/add-plugin` only) before first publish
- Attach release notes: ADR index, activation flow, MCP optional profile
- After publish: enterprise re-audit (Phase 7 EA-506)

## Rollback

- Re-publish previous plugin version
- Consumers: reinstall prior `kit_version` via `cursor_workflow install` from tagged kit release
