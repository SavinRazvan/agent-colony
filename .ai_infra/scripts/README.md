# `.ai_infra/scripts/` — workflow scripts

Pattern A scripts live here. Agents and Makefile invoke **`.ai_infra/scripts/...`** paths.

| Path | Role |
|------|------|
| `pr/` | PR spine — **`prepare.py` owns `resolve_gates()`** (`GATES` = alias) |
| `architecture/` | `check_governance_consistency.py`, `check_debrand.py` |
| `install/` | `scaffold.py` — consumer install |
| `release/` | `sync_plugin_bundle.py` — agents/rules/skills + payload sync (all committed) |
| `dev/` | Maintainer helpers (e.g. local workspace migrate) |
