---
name: merge-pr
description: Final checks, merge via gh, merge.md, finalize git state.
disable-model-invocation: true
---

# Merge PR

**Goal:** Merge only when artifacts + gates are satisfied.

## Steps

1. **Check** (pipeline from user settings when omitted; add `--arch-impacting` for alignment enforcement):  
   `python .ai_infra/scripts/pr/merge.py --pr <id|url> --pipeline default --check-only`  
   Add `--arch-impacting` if alignment artifacts are required (enforces both alignment files; produced by **`enterprise-auditor`** per `enterprise-architecture-audit` skill).
2. No unresolved BLOCKER/IMPORTANT or alignment **P0** without documented acceptance.
3. `python .ai_infra/scripts/pr/verify_publish.py --branch <branch>` and `gh pr view --json headRefName,state`.
4. **PR body:** `python -m cursor_workflow contributors pr-body --summary "…" --pipeline default` → paste into `gh pr create --body-file -`.
5. `gh pr merge <n> --merge` (or repo policy).
6. Note merge SHA: `gh api repos/.../pulls/<n> -q .merge_commit_sha` (or `gh pr view` if working).
7. **Record:**  
   `python .ai_infra/scripts/pr/merge.py --pr <id|url> --pipeline default --merge-sha <sha>`  
   (same `--arch-impacting` if used above). Enrich `merge.md` with method + follow-ups.
8. **Finalize:** `git checkout main`; `python .ai_infra/scripts/pr/finalize.py --branch <branch>`; prune remotes; confirm feature branch gone on origin.

**Detail:** `.agents/skills/pr-workflow/SKILL.md`.
