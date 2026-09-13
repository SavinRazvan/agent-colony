<!--
  Do not edit ## headings. Fill via create-from-template CLI flags
  (--acceptance / --rollback / --notes). Audit scope is kit-process accountability.
-->
## Acceptance

- Audit artifacts written under `.local/workflow-artifacts/` with `Audit-Schema: 1` when findings are recorded
- `## Audit limits` and accountability fields on P0/P1 findings (owner, due_slice, consequence_if_ignored)
- `check_audit_artifacts.py` PASS when schema-1 artifacts exist
- {{acceptance}}

## Rollback

- Remove or archive audit artifacts for this pass; {{rollback}}

## Audit scope

| Field | Value |
|-------|-------|
| **audit_scope** | kit |
| **named_target** | (TBD — repo area or release under review) |
| **commissioned_by** | (TBD) |

## Notes

<!-- agents: Notes lines are auto-timestamped by CLI -->

{{notes}}
