---
name: debug-error-surface
description: Map user-visible errors, exit codes, and exception paths to root-cause hypotheses in debug campaigns.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-error-surface/SKILL.md
Role: Error surface analysis protocol for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Pairs with debug-scripts capture and debug-run-ledger.
-->

# Debug error surface

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- User sees misleading, swallowed, or generic error messages.
- Exit codes from `debug capture` do not match documented CLI contracts.
- Stack traces point across module boundaries; need ruled-out hypotheses.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-scripts/SKILL.md`
- `.cursor/skills/debug-run-ledger/SKILL.md`
- Relevant CLI help and exception handlers in source (read-only)

## Allowed scope

- Trace error propagation: raise site → handler → user message → exit code.
- `analyze --verdict` per run: `confirmed`, `ruled_out`, `probable`, `unknown`.
- DBG findings for behavioral defects; TR for test gaps exposing the surface.

**Out of scope:** changing exception flows on the debug card.

## CLI evidence

```bash
python3 -m agent_colony debug capture --slug <slug> --propagate-exit -- -- <repro>
python3 -m agent_colony debug analyze --slug <slug> --run <run_id> --verdict probable
python3 -m agent_colony debug finding add --slug <slug> --kind DBG --summary "<surface>" --path <file>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Record exact child exit code and `termination_reason` from capture output.

## Completion evidence

- Error surface table: `symptom`, `observed_exit`, `handler_path`, `verdict`, `run_id`.
- At least one ruled-out hypothesis documented with disproof run.
- User-visible message quoted from redacted vault excerpt, not paraphrase alone.

## Handoff

Queue implementer child card for handler fixes. Notes:

```text
Error-surface: verdict=<label> · run=<run_id> · DBG=<id>
```

Shippable severity → `handoff --next verifier` per `debug-protocol`.
