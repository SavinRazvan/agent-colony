<!--
File: instrumentation-map.template.md
Path: .ai_infra/templates/debug-campaign/instrumentation-map.template.md
Role: Probe and instrumentation map template.
Used By:
 - agent_colony debug init
Depends On:
 - vault/probes/index.json
-->

# Instrumentation Map

## Active Probes

(none)

## Removed Or Promoted Probes

(none)
# Instrumentation map — {{slug}}

| probe_id | file | marker | state | rollback | owner |
|----------|------|--------|-------|----------|-------|
| {{probe_rows}} |
