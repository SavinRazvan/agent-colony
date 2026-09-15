---
name: debug-module-map
description: Campaign-scoped module topology map for locating failure boundaries during forensic investigation.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-module-map/SKILL.md
Role: Module-level topology evidence for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Advisory for investigation; not an enterprise audit substitute.
-->

# Debug module map

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Failure span is unclear across packages or install boundaries.
- `debug inventory` shows untracked paths near the repro surface.
- Hypothesis needs dependency / dependent ranking before experiments.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-file-ledger/SKILL.md`
- `AGENTS.md`, `README.md`, `tests/modules/*`
- Compare depth style with `.cursor/skills/audit-module-map/SKILL.md` (audit-only sibling)

## Allowed scope

- Read-only repo traversal; register map artifacts under the campaign.
- Per-module: goal, entrypoints, contracts, importance, dependencies, test ownership.
- Label uncertain ownership `TBD` with follow-up probe or child card.

**Out of scope:** auto-remediation, CHK-* scorecards, merge prep.

## CLI evidence

```bash
python3 -m agent_colony debug inventory --slug <slug>
python3 -m agent_colony debug artifact register --slug <slug> --skill-id debug-module-map --path <rel>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Cite `tracked` / `untracked` digest from `inventory` and registered artifact SHA.

## Completion evidence

- Map artifact lists `source_paths`, `test_paths`, and `gaps_or_risks` per module.
- Every production module touched by repro has an entry or explicit `TBD`.
- Findings reference module boundaries with repo paths, not chat paraphrase.

## Handoff

Fold map into DBG findings or `debug note`. For structural remediation spanning modules, open implementer child card with map artifact path and `debug finding add --kind DBG`.
