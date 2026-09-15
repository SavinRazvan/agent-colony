---
name: debug-handoff
description: Close debugger campaigns with findings, child cards, publish manifest, and verifier-ready board Notes.
---
<!--
File: SKILL.md
Path: .cursor/skills/debug-handoff/SKILL.md
Role: Campaign exit and downstream handoff protocol for debugger agent.
Used By:
 - .cursor/agents/debugger.md
Depends On:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .cursor/skills/evidence-first/SKILL.md
Notes:
 - Shippable cards require verifier hop before Done (board-ssot).
-->

# Debug handoff

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Hypothesis loop complete; findings curated for DBG / TR / SG rows.
- Probes resolved; publish manifest ready.
- Ready for implementer child work, verifier review, or human decision.

## Read first

- `.cursor/skills/debug-protocol/SKILL.md`
- `.cursor/skills/board-ssot/SKILL.md` § Verifier-before-Done
- `.cursor/skills/evidence-first/SKILL.md`
- Campaign `publish/` manifest and `finding render` output

## Allowed scope

- Render findings, update finding status, link child board cards.
- CLI handoff payload and board Notes with manifest hash.
- `debug close` only after `validate --final` passes.

**Forbidden:** Done on shippable cards without `--agent verifier` or documented allow-skip.

## CLI evidence

```bash
python3 -m agent_colony debug finding render --slug <slug>
python3 -m agent_colony debug finding update --slug <slug> --id <id> --status <open|queued|closed> --child-card <url>
python3 -m agent_colony debug handoff --slug <slug> --next-agent <implementer|verifier|human> --outcome ready
python3 -m agent_colony debug validate --slug <slug> --final
python3 -m agent_colony debug close --slug <slug> --outcome closed
python3 -m agent_colony debug status --slug <slug>
```

Record PASS from `validate --final` and close in this run.

## Completion evidence

- DBG/TR/SG rows rendered; child cards queued for behavioral work.
- Board Notes cite `publish/` manifest hash and validation PASS.
- Campaign immutable after `close`; supersede for follow-up investigation.

## Handoff

Board Pattern A:

```bash
python3 -m agent_colony project handoff --last --agent debugger --next <peer> --to in_review
```

Line format:

```text
item_id=<PVTI_…> · campaign=<slug> · @owner.github_user/debugger · Status=in_progress→in_review
next=@owner.github_user/<peer> · publish=<sha256> · Evidence: Verified | Partial
```

Shippable → `next=verifier` before Done.
