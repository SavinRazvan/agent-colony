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
 - This product ships **7** always-applied rules under `.cursor/rules/` (6 kit + `project-ssot-precedence`).
 - Additional product rules may also live in `overlays/rules/` (copy at install).
 - Last reviewed: 2026-07-19
-->

# Rules overlap matrix (Cursor)

| Rule file | Purpose | Overlap with | Posture |
|-----------|---------|--------------|---------|
| `pr-workflow-enforcement.mdc` | PR-first, artifacts, merge gates | `workflow-complete.md`, `pr-workflow/SKILL.md` | **Short pointer** to `local_workflow_paths.py` + `prepare.py` `resolve_gates()` (`GATES` = 2-gate alias) |
| `implementation-workflow-governance.mdc` | Slice lifecycle, planning discipline, testing, evidence-first | `implementer.md`, `token-efficiency.md`, `evidence-first` | **Keep** |
| `advisory-audit-alignment-enforcement.mdc` | Alignment artifacts (authored via `auditor`) | `agent-workflow-procedures.md` | **Keep** |
| `commit-trailer-format.mdc` | Required commit trailers + optional `Assisted-by` (no `Made-with:`) | `README.md`, `AGENTS.md` § Commits | **Keep separate** |
| `file-docstring-header-relations.mdc` | File headers | All new source files | **Keep** |
| `local-artifact-protection.mdc` | `.coverage`, `.env` (project paths) | ops runbooks | **Keep** |
| `project-ssot-precedence.mdc` | Board SSOT precedes local trackers when `project_ssot.enabled` (ADR-008) | `board-ssot` skill, ADR-008 | **Keep** (product SSOT; also under `overlays/rules/`) |

## Not in universal core

| Rule / pack | Location | Notes |
|-------------|----------|-------|
| Extra product-specific rules (e.g. adapter wall) | `overlays/rules/*.mdc` | Install via `cp overlays/rules/*.mdc target/.cursor/rules/` — beyond the 7 shipped here |

## Track D status

- **D0 inventory:** this matrix (**7** shipped rules: 6 kit + `project-ssot-precedence`).
- **D1 concise pass:** applied — short invariants + links to `prepare.py`.
- **D2 merge/remove:** `test-implementation-standard.mdc` **removed** (content in `implementation-workflow-governance.mdc`).
