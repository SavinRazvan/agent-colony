<!--
File: rules-overlap-matrix.md
Path: .ai_infra/docs/governance/rules-overlap-matrix.md
Role: Inventory of `.cursor/rules/*.mdc` overlaps and merge posture (Track D).
Used By:
 - Maintainers changing Cursor rules
Depends On:
 - AGENTS.md
 - docs/operations/agent-workflow-procedures.md
Notes:
 - Universal MAS Workflow Kit: **6** always-applied rules under `.cursor/rules/`.
 - Product rules (e.g. adapter wall) live in `overlays/rules/`.
 - Last reviewed: 2026-06-14
-->

# Rules overlap matrix (Cursor)

| Rule file | Purpose | Overlap with | Posture |
|-----------|---------|--------------|---------|
| `pr-workflow-enforcement.mdc` | PR-first, artifacts, merge gates | `workflow-complete.md`, `pr-workflow/SKILL.md` | **Short pointer** to `local_workflow_paths.py` + `prepare.py` `GATES` |
| `implementation-workflow-governance.mdc` | Slice lifecycle, planning discipline, testing, anchoring | `implementer.md`, `token-efficiency.md` | **Keep** |
| `advisory-audit-alignment-enforcement.mdc` | Alignment artifacts (authored via `enterprise-auditor`) | `agent-workflow-procedures.md` | **Keep** |
| `commit-trailer-format.mdc` | Required commit trailers + optional `Assisted-by` (no `Made-with:`) | `README.md`, `AGENTS.md` § Commits | **Keep separate** |
| `file-docstring-header-relations.mdc` | File headers | All new source files | **Keep** |
| `local-artifact-protection.mdc` | `.coverage`, `.env` (project paths) | ops runbooks | **Keep** |

## Not in universal core

| Rule / pack | Location | Notes |
|-------------|----------|-------|
| Product-specific rules (e.g. adapter wall) | `overlays/rules/*.mdc` | Install via `cp overlays/rules/*.mdc target/.cursor/rules/` — not shipped in core |

## Track D status

- **D0 inventory:** this matrix (6 universal rules).
- **D1 concise pass:** applied — short invariants + links to `prepare.py`.
- **D2 merge/remove:** `test-implementation-standard.mdc` **removed** (content in `implementation-workflow-governance.mdc`).
