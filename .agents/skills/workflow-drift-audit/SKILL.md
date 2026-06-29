---
name: workflow-drift-audit
description: Operational workflow drift audit; canonical protocol under .cursor/skills/.
disable-model-invocation: true
---

# Workflow drift audit (entry)

## Goal

Run **drift validate** first and record operational drift findings where other agents can find them.

## Canonical protocol

**Full instruction set:** `.cursor/skills/workflow-drift-audit/SKILL.md`

**Agent card:** `.cursor/agents/workflow-drift-guard.md`

## Outputs (gitignored)

| Artifact | Path |
|----------|------|
| Drift report | `.local/workflow-artifacts/drift/drift-audit.md` |
| Action backlog | `.local/workflow-artifacts/drift/drift-todos.md` |

## Exit criteria

Matches the canonical skill: script run captured, both artifacts written, P0 count explicit.
