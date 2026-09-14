# Kit verification preflight artifacts

**Tier 2 runtime** machine-readable outputs from maintainer verification commands and auditor depth passes.

| File / path | Writer |
|-------------|--------|
| `preflight.json` | `python -m agent_colony verify all` |
| `doc-facts-preflight.json` | `python -m agent_colony doc validate` |
| `agent-surface/<id>.md` | `auditor` + skill `agent-surface-parity` (per-agent doc/canvas vs machine matrix) |

See `.ai_infra/docs/operations/local-workspace-layout.md`.
