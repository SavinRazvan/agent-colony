# Research corpus workflow

**Brief-driven multi-round research** for `_research_results/` — not implementation slices (`implementer` + board / `.local/.../current/*`).

**Status (2026-07-19):** Agent is **shipped and proven** (live external pack + verifier PASS). Corpus packs remain **opt-in** — they appear only after `research init` (not an incomplete agent).

Versioned hub (in git). Corpus boundaries: `_research_results/RESEARCH_BOUNDARIES.md` (from `research init`).

## Order (active)

1. `.cursor/agents/researcher.md` — **Adaptive intake** (chat / peer agents / board)
2. `.cursor/skills/research-corpus/SKILL.md`
3. Normalize source → `research init` → `research fetch` → rounds → `validate`
4. Pack `BRIEF.md` + `SOURCE.md` under `_research_results/sources/<slug>/`

Agent: **`.cursor/agents/researcher.md`**. Canvas: `canvases/agent-researcher.canvas.tsx`.

## How it works (7 steps)

1. **Intake** — normalize source + question → `BRIEF.md` (defaults for terse `/researcher <url>`)
2. **Init/fetch** — CLI scaffolds pack + shallow clone to `cache/<slug>/`
3. **Map/extract** — `MAP.md` + `findings/<lens>.md` with path + ~Lnn evidence
4. **Deepen** — `rounds/round-N.md` only for open questions (cap ≤6; anti-loop)
5. **Curate/pack** — `CURATED.md` → `AGENT_BRIEF.md` → `INDEX.json` `status=complete`
6. **Validate** — `python3 -m cursor_workflow research validate --slug <slug>` PASS
7. **Exit** — research card Done + Notes with pack paths; handoff to consumer

## Hard boundary

No product repo edits; no git commits for research packs; writes only `_research_results/`.

## Decisions

| # | Choice |
|---|--------|
| D0 | No edits outside `_research_results/` |
| D1 | No git commits / PRs for research-only work |
| D2 | External runs require a Brief — **derive from chat/handoff/card** if not pasted formally |
| D3 | Pin every pack (path or commit SHA) in `SOURCE.md` |
| D4 | Consumers read `AGENT_BRIEF.md` + `INDEX.json`, not the whole foreign tree |
| D5 | CLI owns init/fetch/validate; agent owns rounds 1–6 prose evidence |
| D6 | Host `mode: self` is optional; default is `external` when a source is present |
| D7 | Accept HTTPS GitHub URLs and terse `/researcher <url>` chat; apply skill defaults |
| D8 | Anti-loop: rounds_max≤6; no re-fetch/re-init without `--force`; exit on complete |
| D9 | Private GitHub needs consumer `gh`/git auth; public needs network only |
| D10 | Agent shipped/proven; corpus remains opt-in after first `research init` |

## Forbidden

| Action | Why |
|--------|-----|
| `git commit` / PR for research | D1 |
| Edit outside `_research_results/` | D0 |
| External run without any source (and not self) | D2 |
| Invent evidence without path/~Lnn | Evidence contract |
| Implement fixes in product tree during research | → implementer |
| Refuse terse chat that clearly names a GitHub/local source | D7 — adapt + defaults |
| Endless deepen / re-fetch after complete | D8 — stop rules |
| Silent private-clone retry without auth | D9 — one attempt, report fail |

## Pack outputs

| Write here | For |
|------------|-----|
| `sources/<slug>/BRIEF.md` | Intake |
| `SOURCE.md` / `MAP.md` / `findings/*.md` | Rounds 1–3 |
| `rounds/round-N.md` | Deepen |
| `CURATED.md` / `AGENT_BRIEF.md` / `INDEX.json` | Curate + pack |
| `cache/<slug>/` | Shallow GitHub clone (optional) |

## Board

`create-from-template --template research --priority p2` → claim → Done + Notes with pack paths.

## Live proof

| Field | Evidence |
|-------|----------|
| Slug | `flexiai-toolsmith` (Issue #74) |
| Source | `github:SavinRazvan/flexiai-toolsmith` @ `3f8b0c7` |
| Result | 6 rounds · 18 curated · validate PASS · verifier Claim A+B VERIFIED |

## Related

| Workflow | Path |
|----------|------|
| PR merge | `pr-workflow/SKILL.md` |
| Implementation | `implementer` (reads `AGENT_BRIEF.md`) |
| Integration | `integrator` |
| Audit | `enterprise-auditor` |
| Agent canvas | `canvases/agent-researcher.canvas.tsx` |
