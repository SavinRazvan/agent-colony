---
name: audit-alignment
description: DEPRECATED — use enterprise-auditor; alignment outputs unchanged for merge gates.
disable-model-invocation: true
---

# Audit alignment (deprecated stub)

**Do not use this file as the primary workflow.** The canonical audit agent is **`enterprise-auditor`**.

- **Agent:** `.cursor/agents/enterprise-auditor.md`
- **Protocol:** `.cursor/skills/enterprise-architecture-audit/SKILL.md`
- **Merge-gate outputs (unchanged):** `.local/workflow-artifacts/alignment/alignment-audit.md`, `alignment-todos.md` per `.ai_infra/docs/roadmap/alignment-audit-schema.md`
- **Rule:** `.cursor/rules/advisory-audit-alignment-enforcement.mdc`

For architecture-impacting PRs, run a **focused alignment pass** (see enterprise skill) unless a **full** `enterprise-architecture-audit.md` report is explicitly requested.

This stub remains so old links and governance scans that mention `audit-alignment/` keep resolving to a clear redirect.
