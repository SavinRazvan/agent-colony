---
name: debug-scripts
description: Secure capture and ingest procedures for repro commands and existing logs in debugger campaigns.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-scripts/SKILL.md
Role: Command capture and log ingest protocol for debugger experiments.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Capture runs with caller privileges; not a sandbox.
-->

# Debug scripts

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Reproducing a failure with a bounded command (`debug capture`).
- Importing an existing log or CI artifact (`debug ingest`).
- Timeout, output-limit, or non-zero exit needs structured run evidence.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-vault/SKILL.md`
- `.cursor/skills/debug-run-ledger/SKILL.md`
- `.ai_infra/install/agent_colony/debug_capture.py` (limits and termination reasons)

## Allowed scope

- Read-only or diagnostic commands aligned with the campaign hypothesis.
- POSIX capture only; refuse native Windows spawn before experiment.
- Bounded `--timeout` (1–7200 s) and output budgets per campaign.

**Hard stops:** production/staging probes without approval, destructive commands, auth/payment/PII boundaries → `debug block` and human decision.

## CLI evidence

```bash
python3 -m agent_colony debug capture --slug <slug> -- -- <argv...>
python3 -m agent_colony debug capture --slug <slug> --timeout 120 --propagate-exit -- -- <argv...>
python3 -m agent_colony debug ingest --slug <slug> --file <path>
python3 -m agent_colony debug analyze --slug <slug> --run <run_id> --verdict <confirmed|ruled_out|probable|unknown>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Record `run_id`, `child_exit_code`, `termination_reason`, and artifact path from output.

## Completion evidence

- Each experiment has a run directory under `<campaign>/runs/<run_id>/`.
- `analyze` drafted Signals summary with explicit verdict label.
- Session notes appended: `debug note --text "…" --agent debugger`.

## Handoff

Route confirmed behavioral defects to implementer child cards via `debug finding add` (DBG) and `debug-handoff`. Keep raw capture in vault; cite `run_id` in finding summary.
