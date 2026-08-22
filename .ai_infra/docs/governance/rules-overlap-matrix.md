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
 - Kit 0.7.0: **4** always-applied + **3** requestable (load at commit, new files, architecture-impacting prepare).
 - Last reviewed: 2026-08-22
-->

# Rules overlap matrix (Cursor)

| Rule file | alwaysApply | Purpose | Overlap with | Posture |
|-----------|-------------|---------|--------------|---------|
| `pr-workflow-enforcement.mdc` | yes | PR-first, artifacts, merge gates | `workflow-complete.md`, `pr-workflow/SKILL.md` | **Short pointer** to `local_workflow_paths.py` + `prepare.py` `resolve_gates()` |
| `implementation-workflow-governance.mdc` | yes | Slice lifecycle, planning discipline, testing, evidence-first | `implementer.md`, `token-efficiency.md`, `evidence-first` | **Keep** |
| `advisory-audit-alignment-enforcement.mdc` | requestable | Alignment artifacts (authored via `auditor`) | `agent-workflow-procedures.md` | Load before architecture-impacting `/prepare-pr` |
| `commit-trailer-format.mdc` | requestable | Required commit trailers + optional `Assisted-by` | `README.md`, `AGENTS.md` § Commits | Load at commit time |
| `file-docstring-header-relations.mdc` | requestable | File headers | All new source files | Load on new sources |
| `local-artifact-protection.mdc` | yes | `.coverage`, `.env` (project paths) | ops runbooks | **Keep** |
| `project-ssot-precedence.mdc` | yes | Board SSOT precedes local trackers when `project_ssot.enabled` (ADR-008) | `board-ssot` skill, ADR-008 | **Keep** |

## Not in universal core

| Rule / pack | Location | Notes |
|-------------|----------|-------|
| Extra product-specific rules (e.g. adapter wall) | `overlays/rules/*.mdc` | Install via `cp overlays/rules/*.mdc target/.cursor/rules/` — beyond the 7 shipped here |

## Track D status

- **D0 inventory:** this matrix (**7** rules: **4** alwaysApply + **3** requestable; GOV-RULES-001).
- **D1 concise pass:** applied — short invariants + links to `prepare.py`.
- **D2 merge/remove:** `test-implementation-standard.mdc` **removed** (content in `implementation-workflow-governance.mdc`).
