---
name: debug-vault
description: Redacted vault layout, retention rules, and protected-path handling for debugger campaign evidence.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-vault/SKILL.md
Role: Vault and redaction contract for debugger campaigns.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Vault paths are protected per local-artifact-protection.mdc.
-->

# Debug vault

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- After `debug init` — before first `capture` or `ingest`.
- Redaction failure or suspected secret in captured output.
- Human asks what may be published vs kept in vault only.

## Read first

- `.local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md`
- `.cursor/rules/local-artifact-protection.mdc`
- `.cursor/skills/debug-protocol/SKILL.md`
- `.ai_infra/install/agent_colony/debug_redaction.py` (when redaction behavior is unclear)

## Allowed scope

- Read and append under `<campaign>/vault/**` and curated `publish/**`.
- Register artifacts: `debug artifact register --skill-id <id> --path <rel>`.
- Refuse init/capture when size budgets or free-space floors fail.

**Forbidden:** delete, overwrite, unlock-repair, archive, or purge `vault/**` without explicit human approval and a listed target set.

## CLI evidence

```bash
python3 -m agent_colony debug status --slug <slug>
python3 -m agent_colony debug inventory --slug <slug>
python3 -m agent_colony debug validate --slug <slug>
python3 -m agent_colony debug repair --slug <slug> --check
```

Cite tracked vs untrusted counts from `inventory` and any `validate` errors.

## Completion evidence

- No intentional secrets in vault; redaction markers documented in run metadata.
- `publish/` contains only curated, redacted excerpts — manifest hash in Notes.
- Closed campaigns immutable; new work uses `debug init --supersedes <old-slug>`.

## Handoff

On redaction or retention blockers:

```bash
python3 -m agent_colony debug block --slug <slug> \
  --reason "<short>" --evidence "<path-or-command>" \
  --human-state "<needed decision>" --next-action "<ask>"
```

Line for Notes: `Vault: Verified | Partial | Blocked — <one-line gap>`
