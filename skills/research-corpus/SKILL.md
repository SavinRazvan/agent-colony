---
name: research-corpus
description: Brief-driven multi-round research into _research_results packs (external GitHub/local or host self).
---

# Research corpus

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
3. **Board card** — `create-from-template --template research --priority p2` body Brief table
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
- **consumers:** implementer, integrator (plus the requesting agent if known)
- **rounds_max:** 6

Refuse **only** when there is no source and no `mode: self` ask. Missing question → use default and state it in board Notes / chat.

### GitHub access

| Visibility | Requirement |
|------------|-------------|
| Public | Network + `gh` or `git` clone |
| Private | Same, plus consumer auth (`gh auth login` / git credentials that can clone the URL) |

Clone failures: report once and stop — no retry loop.

### Brief contract (persisted)

Write via `research init` into `BRIEF.md`:

```text
source: github:owner/repo@ref | https://github.com/… | path:/abs/or/rel
question: <what MAS / requesting agent needs>
lenses: [architecture, cli, agents, skills, tests, decisions, patterns]
rounds_max: 6
consumers: [implementer, integrator, …]
slug: <derived or explicit>
```

## Procedural setup

```bash
python3 -m cursor_workflow research init --slug <slug> --source '…' --question '…'
python3 -m cursor_workflow research fetch --slug <slug> --source '…'
```

`--source` accepts HTTPS GitHub URLs, `github:…`, `path:…`, or bare local path. Fetch prefers `gh repo clone` (private-friendly), else `git clone --depth 1` into `_research_results/cache/<slug>/`. Re-fetch requires `--force`.

## Anti-loop (hard stop)

| Rule | Behavior |
|------|----------|
| Cap | Deepen ≤ `rounds_max` (default 6); never round 7+ |
| Idempotent init/fetch | Existing pack / `SOURCE.md` → refuse unless `--force` |
| Closed pack | `INDEX.status=complete` + validate PASS → **exit**; do not deepen again unless user reopens |
| Failures | One clone attempt; surface error; stop |
| Gaps | Remaining questions → document gaps; set `blocked` or complete with gaps — do not spin |

## Multi-round loop (active)

Work only under `_research_results/sources/<slug>/`. Read foreign trees read-only.

1. **Scout** — confirm `SOURCE.md` pin (SHA/path); note languages/size.
2. **Map** — write `MAP.md` (entrypoints, layout, docs).
3. **Extract** — for each lens in Brief, fill `findings/<lens>.md` with path + line evidence.
4. **Deepen** — open questions only → `rounds/round-N.md` (N ≤ `rounds_max`). **Stop deepening when N == rounds_max.**
5. **Curate** — `CURATED.md` rows `verified: path; ~Lnn; note: …`.
6. **Pack** — `AGENT_BRIEF.md` (1–2 pages) + update `INDEX.json` (`status: complete`, findings array, `curated_count`, `rounds_completed` ≤ `rounds_max`).
7. **Validate** — `python3 -m cursor_workflow research validate --slug <slug>`.
8. **Exit** — board Done + Notes with pack paths; handoff to named consumer (requesting agent if known). **Then stop.**

## Mode: self (optional)

If `DEPTH_BACKLOG.md` exists and user asks for host deepening: one backlog ID per session; same hard stop; still write under `_research_results/` only.

## Lenses (default)

`architecture` · `cli` · `agents` · `skills` · `tests` · `decisions` · `patterns`

## Output format

```text
slug · mode · rounds · curated_count · AGENT_BRIEF path · validate PASS/FAIL · next consumer
```

## Status

**Agent shipped/proven** (2026-07-19): live external pack (`flexiai-toolsmith`, 18 curated, validate PASS) + verifier Claim A (efficiency) / Claim B (correctness) VERIFIED. Corpus remains **opt-in** after first `research init` — not an incomplete agent. Canvas: `canvases/agent-researcher.canvas.tsx`.
