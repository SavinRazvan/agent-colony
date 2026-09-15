<!--
  Do not edit ## headings. Fill via create-from-template CLI flags
  (--acceptance / --rollback / --notes). Debug brief table may be edited after create.
  Prefer Priority p2 for forensic cards unless PR-linked / shippable severity.
-->
## Acceptance

- Campaign init under `.local/workflow-artifacts/debug/<slug>/`; `debug validate --slug <slug>` PASS for current status
- Publish pack cites Signals + vault_ref; findings rendered (DBG-*/TR-*/SG-*) with child bug/slice payloads when actionable
- Probes cleaned or assigned; campaign `ready_for_consumer` then debugger `debug close` before Done
- {{acceptance}}

## Rollback

- Close or archive campaign under `.local/workflow-artifacts/debug/<slug>/` (do not delete vault without human approval); revert probes first; {{rollback}}

## Debug brief

| Field | Value |
|-------|-------|
| **mode** | incident \| standardize \| structural \| deep |
| **slug** | (TBD) |
| **lenses** | repro, control-error, data-state, concurrency, resource, memory, performance, integration |
| **budgets** | max_runs=20 · stream=16MiB · campaign=512MiB |
| **consumers** | implementer, test-runner |
| **human_status** | not_required \| pending \| approved \| blocked |
| **scope** | (TBD include/exclude) |

## Notes

<!-- agents: Notes lines are auto-timestamped by CLI -->

{{notes}}
