---
name: prepare-pr
description: Make PR merge-ready — fixes, gates via prepare.py, prep artifact.
disable-model-invocation: true
---

# Prepare PR

**Goal:** Green gates + documented evidence in `prep.md`.

## Steps

1. `review.md` exists; clear BLOCKER/IMPORTANT items first.
2. Alignment files present when required (authored via **`enterprise-auditor`** / `enterprise-architecture-audit` skill; see `advisory-audit-alignment-enforcement.mdc`); no open **P0** unless explicitly accepted.
3. Fixes **only** in PR scope.
4. Run (owner from YAML; **Agent/s** auto-merges trackers + pipeline unless `--agents` set):  
   `python .ai_infra/scripts/pr/prepare.py --pr <id|url> --pipeline default`  
   Same **`--agents-from-session`** behavior as review — see **`pr-workflow/SKILL.md`**.  
   (Uses `GATES` in `prepare.py`; on failure, fix and re-run.)  
   If gates were already run and recorded elsewhere: `--skip-gates` to stamp `prep.md` only.
5. Sync trackers if status changed — under **`.local/index-and-planning/current/`**: `session-pointer.md`, `change-index.md`, `plan.md`, `work-tracker.md`, `test-plan.md`, `test-index.md` when applicable.
6. Append human notes to `prep.md`: resolved findings, residual risks.

**Exit:** PR ready for `/merge-pr`. **Detail:** `.agents/skills/pr-workflow/SKILL.md`.
