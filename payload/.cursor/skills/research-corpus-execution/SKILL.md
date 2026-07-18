---
name: research-corpus-execution
description: Brief-driven multi-round research into _research_results packs (external GitHub/local or host self).
---

# Research corpus execution

## When

- External research: user or board card supplies a **Research Brief** (source + question + lenses).
- Host deepening (`mode: self`): optional `DEPTH_BACKLOG.md` when present under `_research_results/`.

**Not for:** product code changes, PR merge, `.local/` implementation — use `implementer` / `.agents/skills/pr-workflow/SKILL.md`.

## Agent

**`.cursor/agents/researcher.md`**. Hub: `.agents/skills/RESEARCH_WORKFLOW.md`.

## Read first

1. `_research_results/RESEARCH_BOUNDARIES.md` (via `research init` if missing)
2. Pack `BRIEF.md` (required for `mode: external`)
3. This skill + templates under `.ai_infra/templates/research-corpus/`

## Brief contract (external)

```text
source: github:owner/repo@ref | path:/abs/or/rel
question: <what MAS needs>
lenses: [architecture, cli, agents, skills, tests, decisions, patterns]
rounds_max: 6
consumers: [implementer, integrator-mas-agent, ...]
slug: <optional>
```

No brief → **refuse** external run.

## Procedural setup

```bash
python3 -m cursor_workflow research init --slug <slug> --source '…' --question '…'
python3 -m cursor_workflow research fetch --slug <slug> --source '…'
```

Fetch pins `SOURCE.md` (path or shallow clone under `_research_results/cache/<slug>/`).

## Multi-round loop (active)

Work only under `_research_results/sources/<slug>/`. Read foreign trees read-only.

1. **Scout** — confirm `SOURCE.md` pin (SHA/path); note languages/size.
2. **Map** — write `MAP.md` (entrypoints, layout, docs).
3. **Extract** — for each lens in Brief, fill `findings/<lens>.md` with path + line evidence.
4. **Deepen** — open questions only → `rounds/round-N.md` (N ≤ `rounds_max`).
5. **Curate** — `CURATED.md` rows `verified: path; ~Lnn; note: …`.
6. **Pack** — `AGENT_BRIEF.md` (1–2 pages) + update `INDEX.json` (`status: complete`, findings array, `curated_count`, `rounds_completed`).
7. **Validate** — `python3 -m cursor_workflow research validate --slug <slug>`.
8. **Exit** — board Done + Notes with pack paths; handoff to named consumer.

## Mode: self (optional)

If `DEPTH_BACKLOG.md` exists and user asks for host deepening: one backlog ID per session; same hard stop; still write under `_research_results/` only. Prefer external Brief packs for cross-repo learning.

## Lenses (default)

`architecture` · `cli` · `agents` · `skills` · `tests` · `decisions` · `patterns`

## Output format

```text
slug · mode · rounds · curated_count · AGENT_BRIEF path · validate PASS/FAIL · next consumer
```
