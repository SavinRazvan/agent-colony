<!--
File: module-boundaries.md
Path: .ai_infra/docs/governance/module-boundaries.md
Role: Machine-readable charter for cross-plane boundaries in the MAS Workflow Kit.
Used By:
 - .ai_infra/docs/governance/README.md
 - check_governance_consistency.py (path-drift scans)
Depends On:
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
Notes:
 - Product application code belongs in consumer repos or overlay rules, not universal agents.
-->

# Module boundaries

## Planes

| Plane | Path | May import Python? | May invoke scripts? |
|-------|------|--------------------|---------------------|
| Cursor contract | `.cursor/`, `.agents/` | No | Via documented `python .ai_infra/scripts/...` only |
| Infrastructure | `.ai_infra/scripts/`, `.ai_infra/mcp_servers/` | Yes (kit scripts) | N/A |
| Runtime | `.local/` | No | Read/write artifacts only |

## Rules

1. **`.cursor/` and `.agents/`** — prose, skills, rules only. No embedded gate command lists; point to `prepare.py` `GATES`.
2. **`.ai_infra/scripts/`** — deterministic workflow spine. May read `.local/` only via paths in `local_workflow_paths.py`.
3. **`.ai_infra/mcp_servers/workflow_mcp/`** — wraps scripts; does not reimplement gate logic.
4. **Overlays** (`overlays/rules/`) — product-specific rules and optional gate snippets; copy into consumer `.cursor/rules/` at install.
5. **Kit dev** (`tests/`, maintainer docs) — not installed to consumers by default.

## Forbidden

- Provider SDK imports in `.cursor/` agent files
- Duplicating `GATES` command lists in agent surfaces
- Bare `scripts/pr/` paths in agent surfaces (use `.ai_infra/scripts/pr/`)
