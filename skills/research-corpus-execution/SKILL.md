---
name: research-corpus-execution
description: Pure deep research for _research_results — DEPTH_BACKLOG slices, curated verification, no step-history gates.
---

# Research corpus execution

## When

- Deepening `_research_results/` for refactor-ready inventory.
- Picking work from [DEPTH_BACKLOG.md](../../../_research_results/DEPTH_BACKLOG.md).

**Not for:** code changes, PR merge, `.local/` implementation — use `implementer` / `.agents/skills/pr-workflow/SKILL.md`.

## Agent

**`.cursor/agents/researcher.md`**. Mode: [PURE_DEEP_RESEARCH.md](../../../_research_results/PURE_DEEP_RESEARCH.md).

## Read first

1. [RESEARCH_BOUNDARIES.md](../../../_research_results/RESEARCH_BOUNDARIES.md)
2. [24-enterprise-research-completion-plan.md](../../../_research_results/24-enterprise-research-completion-plan.md)
3. [PURE_DEEP_RESEARCH.md](../../../_research_results/PURE_DEEP_RESEARCH.md)
4. [DEPTH_BACKLOG.md](../../../_research_results/DEPTH_BACKLOG.md) — one `pending` ID, **or** G1–G8 verify / user slice if [PROGRAM-CLOSED](../../../_research_results/optional-deepening/PROGRAM-CLOSED.md)
5. Target synthesis or curated file for that slice

## Depth loop (active)

1. Pick one backlog ID (`P1-*`, `P2-*`, `P3-*`, `P4-*`).
2. Read repo sources read-only; **no git commit**.
3. Write only `_research_results/`.
4. Add/update [enterprise-curated-verified.md](../../../_research_results/manifests/enterprise-curated-verified.md) with `verified: path; tests: ...` or `~Lnn`.
5. Update owning `0N-*.md` when slice requires synthesis depth.
6. `reviews/deep-<slice>.md` — ≥10 spot-checks.
7. `GAP-*` in [10-gaps-and-planned.md](../../../_research_results/10-gaps-and-planned.md) if needed.
8. Mark backlog `done`; update scorecard.

## Manifest regen (optional — off by default)

```bash
.venv/bin/python scripts/dev/generate_research_manifest.py
.venv/bin/python scripts/dev/enrich_research_deep.py
```

Then re-merge curated rows. **Do not** treat enrich exit 0 as complete.

## Legacy (do not use as done)

Steps 0–10, INDEX `passed`, `reviews/step-NN-review.md` — historical breadth pass only.

## Lenses

| Prefix | Lens |
|--------|------|
| `GOV-*` | Product |
| `DOCGOV-*` | Docs IA |
| `MNT-*` | Maintainer |

## Output format

Slice ID • files touched • curated count • review path • gaps • next backlog ID
