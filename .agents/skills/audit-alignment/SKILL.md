---
name: audit-alignment
description: DEPRECATED RETIRE-PENDING — use auditor + auditor-protocol; stub kept for path/DOC count until AA-ROSTER-005 close.
disable-model-invocation: true
---

# Audit alignment (deprecated stub — retire pending)

**Do not use this file as the primary workflow.** The canonical audit agent is **`auditor`**.

- **Agent:** `.cursor/agents/auditor.md`
- **Protocol:** `.cursor/skills/auditor-protocol/SKILL.md` (CHK-* checklists)
- **Merge-gate outputs (unchanged):** `.local/workflow-artifacts/alignment/alignment-audit.md`, `alignment-todos.md` per `.ai_infra/docs/roadmap/alignment-audit-schema.md`
- **Rule:** `.cursor/rules/advisory-audit-alignment-enforcement.mdc`

**Retirement (AA-ROSTER-005):** Folder remains so maintainer skill count (5) and old links resolve. Delete only after updating AGENTS.md / DOC scans / `sync_plugin_bundle` expectations in a dedicated integrator slice.

For architecture-impacting PRs, run a **focused alignment pass** (see `auditor-protocol`) unless a **full** `enterprise-architecture-audit.md` report is explicitly requested.
