---
name: audit-orchestration
description: Orchestrate verify-all preflight and phased Task delegation for enterprise audit closure.
disable-model-invocation: true
---

# Audit orchestration (entry)

## Canonical protocol

**Full instruction set:** `.cursor/skills/audit-orchestration/SKILL.md`

## Quick start

1. `make verify-all` or `python -m cursor_workflow verify all --write-preflight`
2. Task **`enterprise-auditor`** (readonly) → actions file
3. Task **`implementer`** for approved doc-sync only
4. Task **`workflow-drift-guard`** + **`verifier`** at closure
5. Maintainer PR workflow
