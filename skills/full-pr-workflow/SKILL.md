---
name: full-pr-workflow
description: Full maintainer PR path — review → prepare → merge → finalize cleanup.
disable-model-invocation: true
---

# Full PR workflow (maintainer)

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

**Goal:** Merge a PR and clean up the repo (sync `main`, delete branches) via **finalize**.

## Order

1. `review-pr` — findings only; optional **`make drift-validate`** before review when trackers/board status changed. When scope is architecture-impacting, run **`auditor`** and write alignment artifacts per `.cursor/rules/advisory-audit-alignment-enforcement.mdc`.
2. `prepare-pr` — board Status (or tracker sync only if offline fallback) + `prepare.py` (`resolve_gates()` — universal gates; kit-dev auto-appends drift + doc facts when `IMPLEMENTATION-STATUS.md` exists).
3. `merge-pr` — `merge.py` check + `gh pr merge` + `merge.py --merge-sha` (records merge readiness and writes `merge.md`).
4. **`finalize` (mandatory)** — clean repo state:
   - `python .ai_infra/scripts/pr/finalize.py --branch <feature-branch> --pr <n>`
   - Optional: `--delete-merged-local` (also delete other local branches already merged into `main`).
   - After branch cleanup succeeds, best-effort closes the GitHub Issue linked to `--pr`'s board item — opt-in via `conventions.close_linked_issue_on_cleanup` (default `false`). Never gates the finalize exit code; see § After cleanup.

**Per-step detail:** `.agents/skills/review-pr/`, `prepare-pr/`, `merge-pr/`.

## After cleanup

- `finalize.py` writes a deterministic evidence artifact:
  - `.local/workflow-artifacts/pr/finalize.md`
- If `project_ssot.enabled`, board sync remains handled by `merge.py` (non-blocking on failure).
- **Linked Issue closure (opt-in):** when `conventions.close_linked_issue_on_cleanup: true`, `finalize.py` calls `project close-linked-issue --pr <n>` after branch cleanup succeeds. This closes the GitHub Issue linked to the merged PR's board item — never wired to `set-status`/`claim`/`handoff` so it can't race ahead of merge/cleanup evidence. Outcomes are recorded in `finalize.md § Linked Issue Closure` as `PASS` / `SKIPPED` (no linked Issue, already closed, or flag disabled) / `DEFERRED` (gh API error — non-blocking) / `DRY-RUN` (when `finalize.py --dry-run` is used). Rationale: board `Status=Done` and the underlying GitHub Issue `open`/`closed` state are otherwise independent (ADR-008) — this closes that gap only when a maintainer opts in.

