<!--
File: local-plans-index.md
Path: .ai_infra/templates/local-workspace/exemplars/local-plans-index.md
Role: Index for plan-mode snapshots under .local/plans/
Used By:
 - scaffold.py → .local/plans/index.md
Notes:
 - ADR-010. Live plan SSOT: board card (board_only) or plan.md offline — not this dir.
-->

# Local plan snapshots index

Dated plan-mode history only. **Do not** treat rows here as active backlog or slice status.

| Snapshot | Slug | Agent | Board item | Source |
|----------|------|-------|------------|--------|

List: `python3 -m cursor_workflow plan list` · Create: `python3 -m cursor_workflow plan snapshot --slug <slug>` · Human Build bridge: `python3 -m cursor_workflow plan open --slug <slug> [--force]`
