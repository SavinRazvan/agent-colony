---
name: prepare-pr
description: Make PR merge-ready — fixes, gates via prepare.py, prep artifact.
disable-model-invocation: true
---

# Prepare PR

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

**Goal:** Green gates + documented evidence in `prep.md`.

## Steps

1. `review.md` exists; clear BLOCKER/IMPORTANT items first.
2. Alignment files when architecture-impacting (authored via **`auditor`** / `auditor-protocol` skill; see `advisory-audit-alignment-enforcement.mdc`): both `.local/workflow-artifacts/alignment/alignment-audit.md` and `alignment-todos.md` must exist, carry `Audit-Schema: 1`, and **PASS** `python .ai_infra/scripts/workflow/check_audit_artifacts.py --arch-impacting --summary` before `prepare.py`. No open **P0/P1** (`status: open` fails Schema-1). Pipeline `architecture_impacting` / `requires_alignment_artifacts` **enforces** this at merge (not PR-body hint only). (Default 6th prepare gate still skips unstamped leftover files.)
3. Fixes **only** in PR scope.
4. Status sync: when `project_ssot.enabled` and `sync_policy: board_only`, update **board Status/Notes only** — do **not** dual-write competing `in_progress` into local trackers. Local `.local/index-and-planning/current/` files are offline fallback / session pointer only. When SSOT is disabled or offline fallback is active, sync trackers as usual (`session-pointer.md`, `change-index.md`, `plan.md`, `work-tracker.md`, `test-plan.md`, `test-index.md` when applicable).
5. Run (owner from YAML; **Agent/s** auto-merges trackers + pipeline unless `--agents` set):  
   `python .ai_infra/scripts/pr/prepare.py --pr <id|url> --pipeline default`  
   Same **`--agents-from-session`** behavior as review — see **`pr-workflow/SKILL.md`**.  
   **`prepare.py`** runs `resolve_gates()` — universal (`check_testing_artifacts`, `pytest`); **kit-dev** auto-appends `drift validate` + `doc facts` + `sync_plugin_bundle --check` + `check_audit_artifacts --summary` when `IMPLEMENTATION-STATUS.md` exists (**six** total). On failure, fix and re-run.  
   If gates were already run and recorded elsewhere: `--skip-gates --skip-gates-rationale '…'` to stamp `prep.md` only (rationale required). **Refused** when `--pipeline architecture_impacting` (or pipeline with `requires_alignment_artifacts`) — exit 2.
6. **Kit-dev (optional):** when drift/doc gates pass and you need fresh evidence, Task **`drift-guard`** to refresh `.local/workflow-artifacts/drift/drift-audit.md` and `drift-todos.md`.
7. Append human notes to `prep.md`: resolved findings, residual risks.

**Exit:** PR ready for `/merge-pr`. **Detail:** `.agents/skills/pr-workflow/SKILL.md`.
