# Research corpus workflow

**Brief-driven multi-round research** for `_research_results/` — not implementation slices (`implementer` + board / `.local/.../current/*`).

Versioned hub (in git). Corpus boundaries: `_research_results/RESEARCH_BOUNDARIES.md` (from `research init`).

## Order (active)

1. `.cursor/agents/researcher.md` — **Adaptive intake** (chat / peer agents / board)
2. `.cursor/skills/research-corpus-execution/SKILL.md`
3. Normalize source → `research init` → `research fetch` → rounds → `validate`
4. Pack `BRIEF.md` + `SOURCE.md` under `_research_results/sources/<slug>/`

Agent: **`.cursor/agents/researcher.md`**.

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

`create-from-template --template research` → claim → Done + Notes with pack paths.

## Related

| Workflow | Path |
|----------|------|
| PR merge | `pr-workflow/SKILL.md` |
| Implementation | `implementer` (reads `AGENT_BRIEF.md`) |
| Integration | `integrator-mas-agent` |
| Audit | `enterprise-auditor` |
