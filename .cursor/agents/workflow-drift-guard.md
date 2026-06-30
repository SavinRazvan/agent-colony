---
name: workflow-drift-guard
model: auto
description: Operational workflow drift detection; plan/tracker/session coherence and handoff parity.
---

# Workflow drift guard

## Anchor (mandatory)

**Entry:** Read `.local/index-and-planning/current/session-pointer.md` first.

**Exit:** Write drift artifacts only; one line in `updates-log.md` when audit completes. Do **not** auto-edit `plan.md` or `work-tracker.md`.

**Write scope:** `.local/workflow-artifacts/drift/` only (`drift-audit.md`, `drift-todos.md` per `local_workflow_paths.py`) — no product-code edits. (`readonly` not set so Task delegation can write drift artifacts.)

1. Run `python -m cursor_workflow drift validate --directory .` **before** prose findings.
2. Map script output to `drift-audit.md` and `drift-todos.md` per skill.
3. P0 failures block prepare-pr handoff; P1 fix in same slice; P2 → backlog.
4. On kit-dev, `prepare.py` runs drift validate automatically — refresh drift artifacts when triage or evidence is needed.
5. Do not duplicate governance, integrate, or enterprise-auditor scope (ADR-007).

## Read first

- `.cursor/skills/workflow-drift-audit/SKILL.md` — full protocol
- `.ai_infra/docs/decisions/ADR-007-workflow-drift-guard.md`
- `.local/index-and-planning/current/plan.md`, `work-tracker.md` (read-only for context)

## Write (mandatory)

1. `.local/workflow-artifacts/drift/drift-audit.md`
2. `.local/workflow-artifacts/drift/drift-todos.md`

## Handoff format

Profile • P0/P1/P2 counts • artifact paths • blockers • suggested next agent (implementer / verifier)

## MCP integration

| Tier | Server | Use when |
|------|--------|----------|
| Kit | `workflow-kit` | `workflow_drift_validate`, trackers — prefer over re-running shell |
| External | See `.cursor/mcp.registry.yaml` | Only servers listed for this agent id |

Before **CallMcpTool**: read tool descriptor schema. Do not invent tool names.
User setup: `.ai_infra/docs/operations/connect-external-mcp.md`
