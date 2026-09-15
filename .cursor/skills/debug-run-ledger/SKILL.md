---
name: debug-run-ledger
description: Index and correlate capture and ingest runs across a debugger campaign hypothesis timeline.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-run-ledger/SKILL.md
Role: Run-level evidence ledger for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Canonical run ids come from capture/ingest output.
-->

# Debug run ledger

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Multiple experiments exist; need chronological correlation.
- Findings must cite `run_id` not vague "the test run".
- Comparing before/after captures for the same hypothesis.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-scripts/SKILL.md`
- Campaign `runs/` tree and `status` digest

## Allowed scope

- Maintain ledger: `run_id`, `kind` (capture|ingest), `argv|source`, `verdict`, `links`.
- Append `debug note` when ledger state changes materially.
- Register ledger artifact for publish when curated.

**Out of scope:** re-running experiments without new capture/ingest CLI evidence.

## CLI evidence

```bash
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug analyze --slug <slug> --run <run_id> --verdict <label>
python3 -m agent_colony debug note --slug <slug> --text "run <id>: <one line>" --agent debugger
python3 -m agent_colony debug validate --slug <slug>
```

Status digest must list run count consistent with ledger rows.

## Completion evidence

- Every finding row references at least one `run_id` or labels **Unknown**.
- Verdict progression visible: ruled_out hypotheses do not reappear as confirmed without new run.
- Final ledger registered or embedded in `finding render` output.

## Handoff

```text
Run-ledger: <n> runs · confirmed=<c> · ruled_out=<r> · digest=<status-digest>
```

Attach ledger path in `debug handoff` Notes for verifier or implementer.
