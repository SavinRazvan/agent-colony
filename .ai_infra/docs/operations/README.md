<!--
File: README.md
Path: .ai_infra/docs/operations/README.md
Role: Index for universal operational runbooks.
Used By:
 - AGENTS.md
Depends On:
 - .ai_infra/docs/operations/workflow-complete.md
 - .ai_infra/docs/operations/agent-workflow-procedures.md
 - .ai_infra/scripts/pr/README.md
-->

# Operations Index

## Maintainer workflow

- [`workflow-complete.md`](workflow-complete.md) — end-to-end PR checklist
- [`agent-workflow-procedures.md`](agent-workflow-procedures.md) — gate dedup + commit vs PR artifact provenance
- [`gate-matrix.md`](gate-matrix.md) — prepare GATES vs kit-dev gates vs verify
- [`local-workspace-layout.md`](local-workspace-layout.md) — `.local/` contract
- [`.ai_infra/scripts/pr/README.md`](../../scripts/pr/README.md) — PR scripts and artifact paths

## Universal runbooks

- [`consumer-quickstart.md`](consumer-quickstart.md) — adopt the kit in under five minutes
- [`install-dry-run.md`](install-dry-run.md) — detailed install verification checklist
- [`connect-external-mcp.md`](connect-external-mcp.md) — link external MCP servers
- [`mas-infrastructure-integration.md`](mas-infrastructure-integration.md) — add agents/skills/MCP to kit
- [`upgrade-kit.md`](upgrade-kit.md) — reinstall / semver upgrade
- [`project-config.md`](project-config.md) — optional `project.config.yaml` metadata
- [`token-efficiency.md`](token-efficiency.md) — agent read/write contract
- [`documentation-maintenance-checklist.md`](documentation-maintenance-checklist.md) — doc sync when policy changes
- [`logging-and-errors.md`](logging-and-errors.md) — logging baseline
- [`abbreviations-notepad.md`](abbreviations-notepad.md) — shared abbreviations

## Product overlays (not in core)

Copy `overlays/rules/*.mdc` into target `.cursor/rules/` at install.
