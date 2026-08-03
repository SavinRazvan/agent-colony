---
name: drift-audit
description: Run drift validate first; write drift-audit.md and drift-todos.md with evidence contract.
---
<!--
File: SKILL.md
Path: .cursor/skills/drift-audit/SKILL.md
Role: Operational workflow drift audit protocol for plan/tracker/session coherence.
Used By:
 - .cursor/agents/drift-guard.md
Depends On:
 - .ai_infra/docs/decisions/ADR-007-workflow-drift-guard.md
 - .ai_infra/scripts/workflow/check_drift.py
Notes:
 - Advisory-only: no auto-remediation unless user explicitly asks.
-->

# Workflow drift audit

## Goal

Detect **operational workflow drift** — plan ↔ tracker ↔ session-pointer incoherence, **session Board vs export (DRIFT-004b)**, **board vs tracker dual-write (DRIFT-009)**, **board Status vs open PRs / stale In progress (DRIFT-010)**, handoff doc parity, slice-closure signals — without replacing `auditor` or `verifier`.

## When

- Substantive implementer slice closure (recommended)
- Optional pre-review drift pass before PR workflow
- After tracker or handoff doc edits
- When `project_ssot.enabled` — every pass should include board Status evidence

## Steps

1. **Board first (when enabled):** `python -m cursor_workflow project status` and `project list --status in_progress` — cite board Status in artifacts. Optionally refresh the read-only snapshot: `python -m cursor_workflow project export` (never writes Status).
2. **Script:** `python -m cursor_workflow drift validate --directory .` (or `make drift-validate`). On **consumer app projects**, use `--profile consumer`. Include **DRIFT-004b** / **DRIFT-009** / **DRIFT-010** when `project_ssot` board_only is enabled (ADR-007/008).
3. Capture profile, check IDs, severities, and details from output.
4. Write artifacts under `.local/workflow-artifacts/drift/` only.
5. **Board Exit:** set drift-pass card → `done` (or `in_review` if P0/P1 need human). For Confirmed dual-write, Notes on offending card or Ready handoff to board/implementer — do **not** auto-edit `plan.md`, `work-tracker.md`, or `session-pointer.md`.
6. Print handoff line with `item_id` when applicable.

## Evidence contract

| Label | Meaning |
|-------|---------|
| Confirmed | Script output + file path cited |
| Probable | Inference from trackers; label explicitly |
| Unknown | Not verifiable from repo |

## Artifact frontmatter (both files)

```text
Audit-Type: workflow-drift-pass
Audited-By: drift-guard
Action-By: <name>
GitHub-User: <handle>
Date: <ISO-8601>
Profile: kit-dev | consumer
Command: python -m cursor_workflow drift validate --directory . [--profile consumer]
```

**Consumer DRIFT-005:** When `IMPLEMENTATION-STATUS.md` is absent (normal on plugin installs), DRIFT-005 **PASSes (skip)**. A FAIL on the missing file is a **kit false positive** on older payloads — not a consumer app defect. See `consumer-quickstart.md` § Drift on consumer apps.

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

Governance/debrand → `check_governance_consistency.py`. Agent/registry → `integrate validate`. Architecture → `auditor`. Claims → `verifier`.

## Exit criteria

Script run captured; both artifacts written; P0 count explicit; handoff names next agent if blocked.
