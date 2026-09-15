---
name: debug-lenses
description: Select and apply investigation lenses (repro, error, structural, deep) when initializing debugger campaigns.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-lenses/SKILL.md
Role: Lens selection guide for debugger campaign modes and focus areas.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Lenses are declared at init; lazy-load matching debug-* skills.
-->

# Debug lenses

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Choosing `debug init --mode` and `--lenses` before first experiment.
- Scope creep detected — refocus or supersede with tighter lenses.
- Board card type implies incident vs standardize vs structural pass.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/agents/debugger.md` § Loop

| Mode | Typical lenses | Lazy-load skills |
|------|----------------|------------------|
| `incident` | `repro`, `error` | `debug-scripts`, `debug-error-surface`, `debug-run-ledger` |
| `standardize` | `error`, observability | `debug-observability-standard`, `debug-instrumentation` |
| `structural` | module/file topology | `debug-module-map`, `debug-file-ledger` |
| `deep` | all above | load on demand only |

## Allowed scope

- Set lenses at init; document changes in `debug note` if mid-campaign pivot.
- Match experiment budget to lens depth — do not run `deep` captures under incident SLA without approval.

**Out of scope:** changing `item_id` or board Status from this skill alone.

## CLI evidence

```bash
python3 -m agent_colony debug init --slug <slug> --item-id <PVTI_…> --mode incident --lenses repro,error
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
```

Init PASS line must echo slug, mode, and lens list in campaign metadata.

## Completion evidence

- Campaign metadata lenses match actual work performed (or note documents pivot).
- Each active lens has at least one artifact or explicit **Unknown** gap.
- No orphan skills loaded without corresponding evidence rows.

## Handoff

Notes line: `Lenses: <list> · mode=<mode> · gaps=<short>`

Pivot requiring new scope: `debug init --supersedes <old>` rather than overloading closed campaigns.
