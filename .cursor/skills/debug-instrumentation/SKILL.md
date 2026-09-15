---
name: debug-instrumentation
description: Plan and register temporary DEBUG-PROBE markers and diagnostic hooks without shipping product changes on the debug card.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-instrumentation/SKILL.md
Role: Probe registration and cleanup protocol for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - All probes must resolve before debug close.
-->

# Debug instrumentation

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Static analysis insufficient; need runtime probe at a suspect path.
- `debug probe scan` finds existing `DEBUG-PROBE` markers in workspace.
- Experiment requires short-lived logging or assert hooks (human-approved).

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md`
- `.cursor/skills/debug-file-ledger/SKILL.md`

## Allowed scope

- Register probes with id, path, and note — never leave silent edits unregistered.
- Production/staging probes only with explicit human approval → else `debug block`.
- Resolve every probe before `debug close`; scan must be clean or documented exception.

**Forbidden:** permanent product instrumentation merged from the forensic card.

## CLI evidence

```bash
python3 -m agent_colony debug probe register --slug <slug> --probe-id <id> --path <file> --note "<why>"
python3 -m agent_colony debug probe scan --slug <slug>
python3 -m agent_colony debug probe resolve --slug <slug> --probe-id <id> --note "<cleanup>"
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug validate --slug <slug> --final
```

`probe scan` hit count must be 0 at close, or each hit mapped to register+resolve.

## Completion evidence

- Probe registry lists open → resolved lifecycle with timestamps in campaign notes.
- Capture runs reference probe ids when probes affected behavior.
- `validate --final` passes probe hygiene checks.

## Handoff

If probes cannot be removed safely:

```bash
python3 -m agent_colony debug block --slug <slug> --reason "probe cleanup" \
  --evidence "probe scan hits=<n>" --human-state "approve removal" --next-action "human edit"
```

Else hand off durable hooks to implementer child card with TR/DBG linkage.
