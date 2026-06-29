# Research corpus workflow

**Pure deep research** for `_research_results/` — not implementation slices (`implementer` + `.local/.../current/*`).

Versioned hub (in git). Corpus copy: `_research_results/RESEARCH_WORKFLOW.md`.

## Order (active)

1. [RESEARCH_BOUNDARIES.md](../../_research_results/RESEARCH_BOUNDARIES.md)
2. [PURE_DEEP_RESEARCH.md](../../_research_results/PURE_DEEP_RESEARCH.md)
3. [DEPTH_BACKLOG.md](../../_research_results/DEPTH_BACKLOG.md) — one slice per session
4. `.cursor/skills/research-corpus-execution/SKILL.md`
5. [INDEX.MD](../../_research_results/INDEX.MD) — ownership

Agent: **`.cursor/agents/researcher.md`**.

## Hard boundary

No product repo edits; no git commits; writes only `_research_results/`.

## Decisions

| # | Choice |
|---|--------|
| D0 | No edits outside `_research_results/` |
| D1 | No git commits for research |
| D2 | `.local/` paths only in `07` |
| D6 | Pure deep mode — DEPTH_BACKLOG = success criteria |

## Forbidden

| Action | Why |
|--------|-----|
| `git commit` / PR for research | D1 |
| Edit outside `_research_results/` | D0 |
| INDEX `passed` or Phase 2 % as “complete” | Use Tier A checklist |
| Regen manifests without restoring curated file | Wipes verified rows |
| Implement fixes in `src/` during research | implementer |

## Depth outputs

| Write here | For |
|------------|-----|
| `manifests/enterprise-curated-verified.md` | Verified critical paths |
| `reviews/deep-*.md` | Slice QA |
| `DEPTH_BACKLOG.md` | Queue + scorecard |
| `02`–`09`, `10-gaps` | Synthesis + gaps |

## Manifest regen (optional)

```bash
.venv/bin/python scripts/dev/generate_research_manifest.py
.venv/bin/python scripts/dev/enrich_research_deep.py
```

Default: **off**. Re-merge curated after regen.

## Enterprise maturity

| Level | Requirement |
|-------|-------------|
| L2 | Manifest breadth (done) |
| L3 | 15 charter critical paths (done) |
| L3+ Tier A | [DEPTH_BACKLOG.md](../../_research_results/DEPTH_BACKLOG.md) + [enterprise-quality-checklist.md](../../_research_results/reviews/enterprise-quality-checklist.md) |
| L4 | `enterprise-auditor` per [ENTERPRISE_HANDOFF.md](../../_research_results/ENTERPRISE_HANDOFF.md) |

## Program closed

When optional deepening is **closed** ([PROGRAM-CLOSED.md](../../_research_results/optional-deepening/PROGRAM-CLOSED.md)), the researcher **still works** for:

- G1–G8 verification
- Indexing export-only artifacts in `_research_results/` (e.g. archived doc exports)
- User-requested backlog slices (add row to DEPTH_BACKLOG first)

Product fixes → **implementer** · L4 refresh → **enterprise-auditor** (optional).

## Related

| Workflow | Path |
|----------|------|
| PR merge | `PR_WORKFLOW.md` |
| Implementation | `implementer` |
