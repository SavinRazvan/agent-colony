<!--
File: SKILL.md
Path: .cursor/skills/workflow-drift-audit/SKILL.md
Role: Operational workflow drift audit protocol for plan/tracker/session coherence.
Used By:
 - .cursor/agents/workflow-drift-guard.md
 - .agents/skills/workflow-drift-audit/SKILL.md
Depends On:
 - .ai_infra/docs/decisions/ADR-007-workflow-drift-guard.md
 - .ai_infra/scripts/workflow/check_drift.py
Notes:
 - Advisory-only: no auto-remediation unless user explicitly asks.
-->
---
name: workflow-drift-audit
description: Run drift validate first; write drift-audit.md and drift-todos.md with evidence contract.
---

# Workflow drift audit

## Goal

Detect **operational workflow drift** — plan ↔ tracker ↔ session-pointer incoherence, handoff doc parity, slice-closure signals — without replacing `enterprise-auditor` or `verifier`.

## When

- Substantive implementer slice closure (recommended)
- Optional pre-review drift pass before PR workflow
- After tracker or handoff doc edits

## Steps

1. **Script first:** `python -m cursor_workflow drift validate --directory .` (or `make drift-validate`).
2. Capture profile, check IDs, severities, and details from output.
3. Write artifacts under `.local/workflow-artifacts/drift/` only.
4. Do **not** auto-edit `plan.md`, `work-tracker.md`, or `session-pointer.md`.

## Evidence contract

| Label | Meaning |
|-------|---------|
| Confirmed | Script output + file path cited |
| Probable | Inference from trackers; label explicitly |
| Unknown | Not verifiable from repo |

## Artifact frontmatter (both files)

```text
Audit-Type: workflow-drift-pass
Audited-By: workflow-drift-guard
Action-By: <name>
GitHub-User: <handle>
Date: <ISO-8601>
Profile: kit-dev | consumer
Command: python -m cursor_workflow drift validate --directory .
```

## drift-audit.md

Summary, per-check table (ID, severity, pass/fail, detail, evidence path), verdict (GO / blocked on P0).

## drift-todos.md

Open findings with id, severity, evidence, recommendation, status (`open` | `fixed` | `deferred` | `accepted_divergence`).

## Severity handling

| Severity | Action |
|----------|--------|
| P0 | Block prepare-pr handoff until fixed or accepted with rationale |
| P1 | Fix in same slice when possible |
| P2 | Backlog in drift-todos |

## Overlap (do NOT duplicate)

Governance/debrand → `check_governance_consistency.py`. Agent/registry → `integrate validate`. Architecture → `enterprise-auditor`. Claims → `verifier`.

## Exit criteria

Script run captured; both artifacts written; P0 count explicit; handoff names next agent if blocked.
