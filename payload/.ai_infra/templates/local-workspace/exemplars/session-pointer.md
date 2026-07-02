<!--
File: session-pointer.md
Path: .ai_infra/templates/local-workspace/exemplars/session-pointer.md
Role: Exemplar for install → .local/index-and-planning/current/session-pointer.md
Used By:
 - .ai_infra/templates/local-workspace/README.md
Depends On:
 - plan.md, work-tracker.md exemplars
Notes:
 - Legacy symlink: docs/templates/local-workspace/exemplars/
 - Copy to .local on first install. Agents read this before plan.md every session.
-->

# Session pointer

| Field | Value |
|-------|--------|
| **Last updated** | YYYY-MM-DD |
| **Last agent** | implementer |
| **Active slice** | SLICE-ID |
| **Phase** | develop \| review \| prepare \| merge \| audit |
| **Next agent** | implementer |
| **PR** | — |

## Next read (in order)

1. `plan.md`
2. `work-tracker.md`
3. `change-index.md` (if slice active)

## Next action

(describe one concrete step)

## Blockers

None.

## Related artifacts

(optional paths under workflow-artifacts/)
