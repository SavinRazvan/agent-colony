---
name: pr-workflow
description: Maintainer merge path — review-pr, prepare-pr, merge-pr with Pattern A gates.
disable-model-invocation: true
---

# PR workflow (maintainer)

**Implementer work** (trackers, slices) uses `.local/index-and-planning/current/*`, `.cursor/agents/implementer.md`, and `.cursor/rules/implementation-workflow-governance.mdc`. Slice closure: `.ai_infra/docs/operations/workflow-complete.md` §F.

This skill is the **merge path** only: **review → prepare → merge** (slash skills: `review-pr`, `prepare-pr`, `merge-pr`).

## Order

1. `review-pr` — findings only; optional **`make drift-validate`** before review when trackers changed. When scope is architecture-impacting, run **`enterprise-auditor`** and write alignment artifacts per `.cursor/rules/advisory-audit-alignment-enforcement.mdc`.
2. `prepare-pr` — tracker sync + `prepare.py` (`resolve_gates()` — **4** steps on kit-dev: testing artifacts, pytest, drift, doc facts).
3. `merge-pr` — `merge.py` check, `gh pr merge`, finalize repo state.

Per-step detail: `.agents/skills/review-pr/`, `prepare-pr/`, `merge-pr/`.

## After push (before merge)

- `python .ai_infra/scripts/pr/verify_publish.py --branch "$(git branch --show-current)"`
- `gh pr view --json number,url,headRefName,state`

## Gates

Authoritative list: **`resolve_gates()` in `.ai_infra/scripts/pr/prepare.py`** (universal **two** gates; kit-dev auto-appends drift + doc facts → **four**). Add **`check_governance_consistency.py`** when changing governance or `.cursor/` policy.

## Artifacts (under `.local/`)

Tier 1 buckets are scaffolded at install; Tier 2 files are written during work. Layout: [local-workspace-layout.md](../../.ai_infra/docs/operations/local-workspace-layout.md) § Artifact tiers. Path SSOT: `.ai_infra/scripts/pr/local_workflow_paths.py`.

| Phase | Path |
|-------|------|
| Review | `workflow-artifacts/pr/review.md` |
| Prepare | `workflow-artifacts/pr/prep.md` |
| Merge | `workflow-artifacts/pr/merge.md` |
| Alignment | `workflow-artifacts/alignment/alignment-audit.md`, `alignment-todos.md` |

## After merge

1. `git checkout main` && `git fetch --prune origin`
2. `python .ai_infra/scripts/pr/finalize.py --branch <feature-branch>`

Durable checklist: `.ai_infra/docs/operations/workflow-complete.md`. Legacy redirect: `PR_WORKFLOW.md`.
