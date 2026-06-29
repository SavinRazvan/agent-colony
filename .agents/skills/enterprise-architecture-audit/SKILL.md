---
name: enterprise-architecture-audit
description: Enterprise-grade Python architecture audit; canonical protocol lives under .cursor/skills/ with .local artifact outputs.
disable-model-invocation: true
---

# Enterprise Architecture Audit (entry)

## Goal

Run an **evidence-only**, phased **enterprise architecture audit** of this repo and record results where other agents can find them.

## Canonical protocol

**Full instruction set (phases, scorecard, report sections, Python focus, mandatory Evidence contract, focused alignment pass for PRs):**  
`.cursor/skills/enterprise-architecture-audit/SKILL.md`

**Agent card:** `.cursor/agents/enterprise-auditor.md`

## Outputs (gitignored)

| Artifact | Path |
|----------|------|
| Full report | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md` |
| Action backlog | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-audit-actions.md` |

## Cross-workflow

- **Governance drift (P0/P1):** may also populate `.local/workflow-artifacts/alignment/alignment-audit.md` and `alignment-todos.md` using `.ai_infra/docs/roadmap/alignment-audit-schema.md` (advisory).
- **Implementer:** picks up `enterprise-audit-actions.md` → `work-tracker.md` per `.cursor/rules/implementation-workflow-governance.mdc`.

## Exit criteria

Matches the canonical skill: phases complete, scorecard justified, actions file written, unknowns explicit.
