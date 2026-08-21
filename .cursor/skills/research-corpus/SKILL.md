---
name: research-corpus
description: Brief-driven multi-round research into _research_results packs (external GitHub/local or host self).
---

# Research corpus

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- External research: user chat, peer handoff/Notes, or board research card names a source
- Host deepening (`mode: self`): optional `DEPTH_BACKLOG.md` under `_research_results/`

**Not for:** product code, PR merge, `.local/` implementation — use `implementer` / `pr-workflow`.

**Agent:** `.cursor/agents/researcher.md` · Hub: `.agents/skills/RESEARCH_WORKFLOW.md`

## Read first

1. This skill
2. `_research_results/RESEARCH_BOUNDARIES.md` (via `research init` if missing)
3. Incoming chat / board card / peer handoff
4. Pack `BRIEF.md` when continuing a slug

## Intake

Build a Brief from user chat, peer Notes/handoff, board card, or existing `BRIEF.md`.

### Normalize source

| Input | Normalized |
|-------|------------|
| `https://github.com/owner/repo` | OK; also `github:owner/repo` |
| `https://github.com/owner/repo/tree/ref/...` | `github:owner/repo@ref` |
| `github:owner/repo[@ref]` | Canonical |
| Local path | `path:…` or bare path |

**DeepWiki is not a research source locator.** Packs clone from GitHub/`path:`. Optional wiki Q&A: MCP `deepwiki` with `repoName":"owner/repo"` — see `mcp-connect`. Do not pass deepwiki.com URL to `research init --source`.

### Defaults (terse chat)

If only a link/path:

- **question:** Map architecture, entrypoints, patterns for MAS kit; produce `AGENT_BRIEF`.
- **lenses:** architecture, cli, agents, skills, tests, decisions, patterns
- **slug:** repo name, lowercase hyphens
- **consumers:** implementer, integrator (+ requester if known)
- **rounds_max:** 6

Refuse only when no source and no `mode: self`. Missing question → use default; state in Notes.

### GitHub access

Public: network + `gh` or `git`. Private: + consumer auth. Clone failure → report once; stop.

### Brief contract

```bash
python3 -m agent_colony research init --slug <slug> --source '…' --question '…'
python3 -m agent_colony research fetch --slug <slug> --source '…'
```

`--source`: HTTPS GitHub, `github:…`, `path:…`, or local path. Re-fetch needs `--force`.

## Anti-loop (hard stop)

| Rule | Behavior |
|------|----------|
| Cap | ≤ `rounds_max` (default 6) |
| Idempotent | Existing pack → refuse unless `--force` |
| Closed pack | `INDEX.status=complete` + validate PASS → **exit** |
| Failures | One clone attempt; stop |
| Gaps | Document; set `blocked` or complete with gaps |

## Multi-round loop

Work under `_research_results/sources/<slug>/` only. Foreign trees read-only.

1. **Scout** — confirm `SOURCE.md` pin
2. **Map** — `MAP.md`
3. **Extract** — `findings/<lens>.md` with path + line evidence
4. **Deepen** — `rounds/round-N.md` (N ≤ `rounds_max`)
5. **Curate** — `CURATED.md` rows `verified: path; ~Lnn; note: …`
6. **Pack** — `AGENT_BRIEF.md` + `INDEX.json`
7. **Validate** — `research validate --slug <slug>`
8. **Exit** — board Done + Notes; handoff to consumer; **stop**

## Mode: self

One backlog ID per session when `DEPTH_BACKLOG.md` exists and user asks.

## Output

```text
slug · mode · rounds · curated_count · AGENT_BRIEF path · validate PASS/FAIL · next consumer
```

Canvas: `canvases/agent-researcher.canvas.tsx`.
