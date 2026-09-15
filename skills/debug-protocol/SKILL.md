---
name: debug-protocol
description: Orchestration hub for debugger campaigns — init, experiment loop, findings, and close with lazy-loaded debug-* skills.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-protocol/SKILL.md
Role: Master forensic investigation protocol for debugger agent campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Lazy-load other debug-* skills only when the current phase needs them.
-->

# Debug protocol

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Board card is claimed for forensic investigation (`create-from-template --template debug`).
- User or Notes cite a reproducible failure, regression, or standards gap.
- Prior campaign is superseded; start a new slug with `--supersedes`.

## Read first

- `.cursor/agents/debugger.md`
- `.local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md` (after `debug init`)
- `.cursor/skills/evidence-first/SKILL.md`
- Lazy-load by phase:
  - **Vault / redaction** → `debug-vault`
  - **Scripts / capture** → `debug-scripts`
  - **Topology** → `debug-module-map`, `debug-file-ledger`
  - **Standards** → `debug-observability-standard`, `debug-error-surface`, `debug-instrumentation`
  - **Runs** → `debug-run-ledger`
  - **Lens choice** → `debug-lenses`
  - **Exit** → `debug-handoff`

## Allowed scope

- Campaign evidence under `.local/workflow-artifacts/debug/<slug>/` only.
- Hypothesis experiments via `debug capture` / `debug ingest` / `debug analyze`.
- DBG / TR / SG findings, probes, and publish manifest curation.
- Child board cards for behavioral fixes — route product edits to **implementer**.

**Out of scope:** merge gates, Schema-1 audit packs, durable product fixes on the debug card.

## CLI evidence

```bash
python3 -m agent_colony debug init --slug <slug> --item-id <PVTI_…> --mode incident
python3 -m agent_colony debug inventory --slug <slug>
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
python3 -m agent_colony debug validate --slug <slug> --final
```

Record PASS/FAIL and digest from this run. Do not infer from chat alone.

## Completion evidence

- `debug validate --final` exits 0.
- Active probes resolved (`debug probe scan` clean or registered + resolved).
- Findings rendered; publish manifest hash recorded in board Notes.
- Shippable cards: verifier hop before Done.

## Handoff

```text
item_id=<PVTI_…> · campaign=<slug> · @owner.github_user/debugger · Status=<before>→<after>
next=@owner.github_user/<implementer|verifier|human> · publish=<manifest-sha256>
```

Use `python3 -m agent_colony debug handoff --slug <slug> --next-agent <peer> --outcome ready` before board Status change.
