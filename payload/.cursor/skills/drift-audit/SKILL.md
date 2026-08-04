---
name: drift-audit
description: Run drift validate first; write drift-audit.md and drift-todos.md with evidence contract; goal/plan/agent-doctrine pulse.
---
<!--
File: SKILL.md
Path: .cursor/skills/drift-audit/SKILL.md
Role: Continuous goal/plan/agent-doctrine/docs coherence plus operational DRIFT scripts.
Used By:
 - .cursor/agents/drift-guard.md
Depends On:
 - .ai_infra/docs/decisions/ADR-007-workflow-drift-guard.md
 - .ai_infra/scripts/workflow/check_drift.py
Notes:
 - Advisory-only: no auto-remediation unless user explicitly asks.
 - Deep architecture/security/perf is auditor — not this skill.
-->

# Drift audit

## Goal

Detect **operational workflow drift** and a **falsifiable goal/doctrine pulse**:

- plan ↔ tracker ↔ session-pointer incoherence
- **DRIFT-004b** session Board vs export; **DRIFT-009** dual-write; **DRIFT-010** board vs PRs
- **DRIFT-011** `.cursor/agents` basenames == eight live kit agent ids
- Prose goal pulse: board Acceptance/Notes vs plan pointers vs `AGENTS.md` / agent cards (flag gaps; hand off — do not rewrite architecture)

Does **not** replace `auditor` (CHK-* scorecard) or `verifier`.

## When

- Substantive implementer slice closure (recommended)
- After plans / board Acceptance / agent doctrine docs change
- Optional pre-review drift pass before PR workflow
- When `project_ssot.enabled` — every pass should include board Status evidence

## Entry checklist (goal pulse)

1. Board (when enabled): `project status` + `list --status in_progress` — read Acceptance / Notes on In progress cards.
2. Plan pointers: `.local/index-and-planning/current/plan.md` (or board card body as SSOT) — Current focus / goals.
3. Doctrine: `AGENTS.md` skills/agents table vs `.cursor/agents/*.md` (script: DRIFT-011).
4. Docs freshness vs goals: note Probable if AGENTS.md / IMPLEMENTATION-STATUS look stale relative to Current focus (prose only).

## Steps

1. **Board first (when enabled):** `python -m cursor_workflow project status` and `project list --status in_progress` — cite board Status in artifacts. Optionally refresh the read-only snapshot: `python -m cursor_workflow project export` (never writes Status).
2. **Script:** `python -m cursor_workflow drift validate --directory .` (or `make drift-validate`). On **consumer app projects**, use `--profile consumer`. Include **DRIFT-004b** / **DRIFT-009** / **DRIFT-010** / **DRIFT-011** when kit-dev / board_only as applicable (ADR-007/008).
3. Capture profile, check IDs, severities, and details from output.
4. Add prose **Goal pulse** section in drift-audit.md (board/plan/AGENTS gaps). Fuzzy “vision mismatch” stays Probable — not CI.
5. Write artifacts under `.local/workflow-artifacts/drift/` only.
6. **Board Exit:** set drift-pass card → `done` (or `in_review` if P0/P1 need human). For Confirmed dual-write or roster gaps, Notes on offending card or Ready handoff to board/implementer — do **not** auto-edit `plan.md`, `work-tracker.md`, or `session-pointer.md`.
7. Print handoff line with `item_id` when applicable.

## Evidence contract

| Label | Meaning |
|-------|---------|
| Confirmed | Script output + file path cited |
| Probable | Inference from trackers/docs; label explicitly |
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

Summary, per-check table (ID, severity, pass/fail, detail, evidence path), **Goal pulse** subsection, verdict (GO / blocked on P0).

## drift-todos.md

Open findings with id, severity, evidence, recommendation, status (`open` | `fixed` | `deferred` | `accepted_divergence`).

## Severity handling

| Severity | Action |
|----------|--------|
| P0 | Block prepare-pr handoff until fixed or accepted with rationale |
| P1 | Fix in same slice when possible |
| P2 | Backlog in drift-todos |

## Overlap (do NOT duplicate)

Governance/debrand → `check_governance_consistency.py`. Agent/registry deep structure → `integrate validate`. Architecture / CHK-* → `auditor`. Claims → `verifier`.

## Exit criteria

Script run captured; both artifacts written; P0 count explicit; Goal pulse noted; handoff names next agent if blocked.
