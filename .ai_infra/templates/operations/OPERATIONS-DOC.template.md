<!--
File: OPERATIONS-DOC.template.md
Path: .ai_infra/templates/operations/OPERATIONS-DOC.template.md
Role: Template for new operations runbooks under docs/operations/.
Used By:
 - documentation-maintenance-checklist.md
 - integrator-protocol
Depends On:
 - asd-ste100-prose.md
 - file-docstring-header-relations.mdc
Notes:
 - Copy to .ai_infra/docs/operations/<name>.md and fill sections.
-->

# {{TITLE}}

**Use ASD-STE100:** [asd-ste100-prose.md](../docs/operations/asd-ste100-prose.md)

## Purpose

One paragraph: who reads this, when, and what decision it supports.

## Prerequisites

- Cursor · Python 3.11+ · `agent_colony` on PATH or venv
- Link: [permissions-and-prerequisites.md](../docs/operations/permissions-and-prerequisites.md)

## Procedure

1. Step with **one Pattern A command** per action.
2. Expected output (one line; not full stdout paste).
3. Exit criteria.

## Token efficiency

- Prefer CLI digests over full file reads.
- Link [token-efficiency.md](../docs/operations/token-efficiency.md) — do not duplicate gate lists.

## Rollback

How to undo or defer safely.

## Related

- [operations/README.md](../docs/operations/README.md)
- [token-efficiency-program.md](../docs/operations/token-efficiency-program.md)
