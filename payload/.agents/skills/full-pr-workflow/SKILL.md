---
name: full-pr-workflow
description: Full maintainer PR path — review → prepare → merge → finalize cleanup.
disable-model-invocation: true
---

# Full PR workflow (maintainer)

**Goal:** Merge a PR and then clean up the repo (sync `main`, delete local + remote feature branches) with a dedicated **finalize** phase.

## Order

1. `review-pr` — findings only; optional **`make drift-validate`** before review when trackers/board status changed. When scope is architecture-impacting, run **`auditor`** and write alignment artifacts per `.cursor/rules/advisory-audit-alignment-enforcement.mdc`.
2. `prepare-pr` — board Status (or tracker sync only if offline fallback) + `prepare.py` (`resolve_gates()` — universal gates; kit-dev auto-appends drift + doc facts when `IMPLEMENTATION-STATUS.md` exists).
3. `merge-pr` — `merge.py` check + `gh pr merge` + `merge.py --merge-sha` (records merge readiness and writes `merge.md`).
4. **`finalize` (mandatory)** — clean repo state:
   - `python .ai_infra/scripts/pr/finalize.py --branch <feature-branch>`
   - Optional: `--delete-merged-local` (also delete other local branches already merged into `main`).

**Per-step detail:** `.agents/skills/review-pr/`, `prepare-pr/`, `merge-pr/`.

## After cleanup

- `finalize.py` writes a deterministic evidence artifact:
  - `.local/workflow-artifacts/pr/finalize.md`
- If `project_ssot.enabled`, board sync remains handled by `merge.py` (non-blocking on failure).

