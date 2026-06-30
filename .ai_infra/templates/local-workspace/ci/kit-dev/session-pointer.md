<!--
File: session-pointer.md
Path: .ai_infra/templates/local-workspace/ci/kit-dev/session-pointer.md
Role: CI fixture for kit-quality gates → .local/index-and-planning/current/session-pointer.md
Used By:
 - .ai_infra/scripts/ci/seed_kit_workspace.py
Depends On:
 - exemplars/session-pointer.md (same schema)
Notes:
 - CI-specific field values; schema matches install exemplar.
-->

# Session pointer

| Field | Value |
|-------|--------|
| **Last updated** | 2026-06-30 |
| **Last agent** | ci-seed |
| **Active slice** | CI-QUALITY |
| **Phase** | ci-quality-gates |
| **Next agent** | implementer |
| **PR** | — |

## Next read (in order)

1. `plan.md`
2. `.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`

## Next action

```bash
make gates
make drift-validate
```

## Blockers

None.

## Related artifacts

(none — CI fixture)
