<!--
File: run-summary.template.md
Path: .ai_infra/templates/debug-campaign/run-summary.template.md
Role: Deterministic run summary template with frozen Signals block.
Used By:
 - agent_colony debug analyze
Depends On:
 - vault/logs/by-run/<run-id>/meta.json
-->

# Run Summary {{run_id}}

## Signals
- exit_code: {{exit_code}}
- errors:
{{errors}}
- logs:
{{logs}}
- probe_hits:
{{probe_hits}}
- verdict: {{verdict}}
- vault_ref: {{vault_ref}}
- evidence_sha256: {{evidence_sha256}}
# Run {{run_id}} — {{slug}}

| Field | Value |
|-------|-------|
| **capture_kind** | {{capture_kind}} |
| **command** | {{command}} |
| **started_at** | {{started_at}} |
| **ended_at** | {{ended_at}} |
| **module** | {{module}} |
| **lens** | {{lens}} |
| **hypothesis** | {{hypothesis}} |

## Signals

- exit_code: {{exit_code}}
- errors: {{errors}}
- logs: {{logs}}
- probe_hits: {{probe_hits}}
- verdict: {{verdict}}
- vault_ref: {{vault_ref}}
- evidence_sha256: {{evidence_sha256}}

## Notes

{{notes}}
