---
name: research-corpus-execution
description: Brief-driven multi-round research into _research_results packs (external GitHub/local or host self).
---

# Research corpus execution

## When

- External research: user chat, another agent’s handoff/Notes, or a board research card names a source.
- Host deepening (`mode: self`): optional `DEPTH_BACKLOG.md` when present under `_research_results/`.

**Not for:** product code changes, PR merge, `.local/` implementation — use `implementer` / `.agents/skills/pr-workflow/SKILL.md`.

## Agent

**`.cursor/agents/researcher.md`**. Hub: `.agents/skills/RESEARCH_WORKFLOW.md`.

## Read first

1. This skill (intake → rounds)
2. `_research_results/RESEARCH_BOUNDARIES.md` (via `research init` if missing)
3. Incoming chat / board card / peer handoff (see Intake)
4. Pack `BRIEF.md` when continuing a slug

## Intake (adapt — do not require a formal paste)

Build a Brief from **any** of:

1. **User chat** — including terse forms like `/researcher https://github.com/owner/repo`
2. **Peer agents** — board Notes, handoff line, cited `AGENT_BRIEF.md` / pack path, implementer/integrator ask
3. **Board card** — `create-from-template --template research` body Brief table
4. **Existing** `sources/<slug>/BRIEF.md`

### Normalize source

| Input | Normalized |
|-------|------------|
| `https://github.com/owner/repo` | OK for CLI; also record `github:owner/repo` |
| `https://github.com/owner/repo/tree/ref/...` | `github:owner/repo@ref` (CLI accepts HTTPS tree URLs) |
| `github:owner/repo[@ref]` | Canonical |
| Local path | `path:…` or bare path |

### Defaults (terse chat)

If only a link/path is given:

- **question:** Map architecture, entrypoints, and patterns useful to our MAS kit; produce `AGENT_BRIEF` for implementer/integrator.
- **lenses:** architecture, cli, agents, skills, tests, decisions, patterns
- **slug:** repo (or directory) name, lowercase with hyphens
- **consumers:** implementer, integrator-mas-agent (plus the requesting agent if known)
- **rounds_max:** 6

Refuse **only** when there is no source and no `mode: self` ask. Missing question → use default and state it in board Notes / chat.

### Brief contract (persisted)

Write via `research init` into `BRIEF.md`:

```text
source: github:owner/repo@ref | https://github.com/… | path:/abs/or/rel
question: <what MAS / requesting agent needs>
lenses: [architecture, cli, agents, skills, tests, decisions, patterns]
rounds_max: 6
consumers: [implementer, integrator-mas-agent, …]
slug: <derived or explicit>
```

## Procedural setup

```bash
python3 -m cursor_workflow research init --slug <slug> --source '…' --question '…'
python3 -m cursor_workflow research fetch --slug <slug> --source '…'
```

`--source` accepts HTTPS GitHub URLs, `github:…`, `path:…`, or bare local path. Fetch pins `SOURCE.md` (shallow clone under `_research_results/cache/<slug>/` when remote).

## Multi-round loop (active)

Work only under `_research_results/sources/<slug>/`. Read foreign trees read-only.

1. **Scout** — confirm `SOURCE.md` pin (SHA/path); note languages/size.
2. **Map** — write `MAP.md` (entrypoints, layout, docs).
3. **Extract** — for each lens in Brief, fill `findings/<lens>.md` with path + line evidence.
4. **Deepen** — open questions only → `rounds/round-N.md` (N ≤ `rounds_max`).
5. **Curate** — `CURATED.md` rows `verified: path; ~Lnn; note: …`.
6. **Pack** — `AGENT_BRIEF.md` (1–2 pages) + update `INDEX.json` (`status: complete`, findings array, `curated_count`, `rounds_completed`).
7. **Validate** — `python3 -m cursor_workflow research validate --slug <slug>`.
8. **Exit** — board Done + Notes with pack paths; handoff to named consumer (requesting agent if known).

## Mode: self (optional)

If `DEPTH_BACKLOG.md` exists and user asks for host deepening: one backlog ID per session; same hard stop; still write under `_research_results/` only.

## Lenses (default)

`architecture` · `cli` · `agents` · `skills` · `tests` · `decisions` · `patterns`

## Output format

```text
slug · mode · rounds · curated_count · AGENT_BRIEF path · validate PASS/FAIL · next consumer
```
