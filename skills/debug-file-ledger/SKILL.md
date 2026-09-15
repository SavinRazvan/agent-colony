---
name: debug-file-ledger
description: File-level ledger of touched, suspect, and out-of-scope paths for a debugger campaign.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-file-ledger/SKILL.md
Role: File-level evidence ledger for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Complements debug-module-map at finer granularity.
-->

# Debug file ledger

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Repro touches a small set of files; need explicit in/out scope.
- `debug inventory` digest shifts after capture or probe activity.
- Findings must cite exact paths with sha or mtime evidence.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-module-map/SKILL.md`
- Campaign `inventory.json` (after `debug inventory`)

## Allowed scope

- Classify paths: `repro`, `suspect`, `context`, `out_of_scope`.
- Register ledger markdown or JSON under the campaign via `artifact register`.
- Cross-check against `.gitignore` and DEBUG_BOUNDARIES — not a confidentiality boundary.

**Forbidden:** editing product source on the debug card; queue implementer child cards instead.

## CLI evidence

```bash
python3 -m agent_colony debug inventory --slug <slug>
python3 -m agent_colony debug probe scan --slug <slug>
python3 -m agent_colony debug artifact register --slug <slug> --skill-id debug-file-ledger --path <rel>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Record inventory digest before and after material experiments.

## Completion evidence

- Ledger rows: `path`, `role`, `evidence` (command or run_id), `verdict`.
- Suspect files link to at least one run or ingest artifact.
- Out-of-scope files listed to prevent scope creep in findings.

## Handoff

Attach ledger path to `debug finding add --path <primary-suspect>`. Notes line:

```text
File-ledger: <n> repro · <m> suspect · digest=<inventory-digest>
```
