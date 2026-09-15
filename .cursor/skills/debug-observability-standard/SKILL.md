---
name: debug-observability-standard
description: Assess logging, metrics, and trace coverage against kit observability expectations during debug campaigns.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-observability-standard/SKILL.md
Role: Observability standards assessment for debugger SG findings.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Produces SG (standards gap) rows; not production SLO certification.
-->

# Debug observability standard

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Failure is hard to diagnose due to missing or noisy telemetry.
- Campaign mode is `standardize` or lens includes observability gaps.
- Capture output lacks correlation ids, structured fields, or level discipline.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/debug-instrumentation/SKILL.md`
- `.cursor/skills/debug-error-surface/SKILL.md`
- Project logging config and any ops docs under `docs/` or `.ai_infra/docs/`

## Allowed scope

- Compare observed telemetry to documented or de-facto kit patterns.
- SG findings for gaps: missing context, log level misuse, absent metrics hooks.
- Recommend probes or child cards — do not ship instrumentation on debug card.

**Not inspected → Unknown.** Do not certify live SLOs or third-party vendor behavior.

## CLI evidence

```bash
python3 -m agent_colony debug capture --slug <slug> -- -- <diag-cmd>
python3 -m agent_colony debug finding add --slug <slug> --kind SG --summary "<gap>" --severity <low|medium|high>
python3 -m agent_colony debug finding render --slug <slug>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Cite capture `run_id` and log excerpts in vault, not raw secrets in Notes.

## Completion evidence

- Each SG row has path evidence and severity with owner consequence if ignored (P0/P1).
- Standards gaps distinguished from transient incident noise (DBG).
- `finding render` output reviewed before handoff.

## Handoff

```text
SG: <count> gaps · top=<summary> · evidence=<run_id|path>
next=@owner.github_user/implementer for instrumentation child cards
```

Use `debug handoff` when campaign is ready for downstream agents.
