<!--
File: workflow-complete.md
Path: .ai_infra/docs/operations/workflow-complete.md
Role: End-to-end maintainer workflow checklist (durable); complements `.agents/skills/pr-workflow/SKILL.md`.
Used By:
 - Maintainers / local agents
Depends On:
 - .agents/skills/pr-workflow/SKILL.md (canonical maintainer merge path + skill order)
 - docs/operations/agent-workflow-procedures.md (enterprise-auditor + dedup contract)
 - .ai_infra/scripts/pr/README.md (PR scripts vs git commit trailers)
 - .ai_infra/scripts/pr/review.py, .ai_infra/scripts/pr/prepare.py, .ai_infra/scripts/pr/merge.py, .ai_infra/scripts/pr/finalize.py, .ai_infra/scripts/pr/verify_publish.py
 - .ai_infra/scripts/pr/check_testing_artifacts.py
 - .ai_infra/scripts/architecture/check_governance_consistency.py (CI parity)
Notes:
 - Additive only: does not replace skills or scripts. Post-merge cleanup removes **git branches**, not docs.
-->

# Complete workflows (maintainer checklist)

## A) Standard PR slice (happy path)

1. **Branch** — `git checkout -b feature/<scope>` (or `fix/`, `chore/`).
2. **Implement + commit** — follow layer rules; commit trailers (required `Author` / `GitHub-User`, optional `Assisted-by`; no `Made-with:`) per `.cursor/rules/commit-trailer-format.mdc` and `AGENTS.md` § Commits.
3. **Push + PR** — `git push -u origin HEAD` → open PR to `main`.
4. **Publish checkpoint** (before merge workflow):
   - `python .ai_infra/scripts/pr/verify_publish.py --branch "$(git branch --show-current)"`
   - `gh pr view --json number,url,headRefName,state,mergeStateStatus`
5. **Prepare gates (before merge / push)** — run **`python .ai_infra/scripts/pr/prepare.py`** (executes all `GATES` — see `.ai_infra/scripts/pr/prepare.py` for the canonical list). Additionally run **`python .ai_infra/scripts/architecture/check_governance_consistency.py`** when changing governance/workflows.
6. **Skills order (do not skip)** — see `.agents/skills/pr-workflow/SKILL.md`:
   - `review-pr` → `prepare-pr` → `merge-pr`
7. **Artifacts** (must exist before merge; fill with real content):
   - `.local/workflow-artifacts/pr/review.md` — `python .ai_infra/scripts/pr/review.py --pr <id|url> --actor "<name>" --agents "review-pr"` then edit findings.
   - `.local/workflow-artifacts/pr/prep.md` — `python .ai_infra/scripts/pr/prepare.py --pr ... --actor "..." --agents "review-pr | prepare-pr"` (runs gates unless `--skip-gates`).
   - `.local/workflow-artifacts/pr/merge.md` — produced via `merge-pr` / `.ai_infra/scripts/pr/merge.py` when ready.
8. **Finalize after merge** (mandatory):
   - `git checkout main` && sync with `origin`
   - `python .ai_infra/scripts/pr/finalize.py --branch <feature-branch>` (optional `--delete-merged-local`)
   - `git fetch --prune origin` and confirm remote branch gone if policy requires it.

## B) Architecture-impacting PRs (extra gates)

Before `/prepare-pr` / final merge:

1. Run **`enterprise-auditor`** with a **focused alignment pass** (`.cursor/skills/enterprise-architecture-audit/SKILL.md`; merge path in `.agents/skills/pr-workflow/SKILL.md`).
2. Ensure **both** exist (merge script enforces with `--arch-impacting`):
   - `.local/workflow-artifacts/alignment/alignment-audit.md`
   - `.local/workflow-artifacts/alignment/alignment-todos.md`
3. Use `python .ai_infra/scripts/pr/merge.py --pr ... --actor "..." --agents "..." --arch-impacting` when recording merge readiness.

## C) Testing + planning index sync (medium/high risk)

Before final `/prepare-pr`:

1. Map changes → `tests/modules/<area>/`.
2. Follow `.cursor/skills/test-module-coverage/SKILL.md` (local) / test-runner agent profile.
3. Update `.local/index-and-planning/current/test-plan.md` and `test-index.md`.
4. Run `python .ai_infra/scripts/pr/check_testing_artifacts.py`.

## D) Doc / plan sync (when scope shifts)

Follow **`agent-workflow-procedures.md` §5** (one `updates-log` entry; avoid duplicating gate lists).

Update tracked docs and local cockpit as needed:

- Project planning docs and `.local/index-and-planning/current/plan.md`, `work-tracker.md`, `history/updates-log.md`

## E) Release candidate (optional — product overlay)

When cutting an RC in a product repo:

- See your overlay's `overlays/docs/operations/` runbooks and any product-specific release scripts you install alongside the kit.

## F) Implementer slice closure (before handoff)

This is the **implementation agent** end-of-loop on top of sections **C** and **D** — run it before saying a slice is finished:

1. **`.local/index-and-planning/history/updates-log.md`** — append one top entry (summary, validation, next step; no repeated prepare-gate paste — see **`agent-workflow-procedures.md`**).
2. **`.local/index-and-planning/current/work-tracker.md`** — resolve task status; keep one primary `in_progress` across the file.
3. **`test-plan.md` / `test-index.md`** — update when tests or ownership changed.
4. **`coverage-index.md`** — regenerate after any coverage run that matters for the slice (project-specific tooling; see overlay pack if applicable).
5. **`implementation-control-center.html`** — under `.local/agents-control-center/dashboards/`; if you add a tracker, update **`../config/pages.json`** and header **Depends On** comments; keep **Coverage** in sync with **`coverage-index.md`**.
6. **`module-audit.html`** — under `.local/agents-control-center/audits/`; touch only when deliberately refreshing a deep module audit export, not per slice.
7. **`make drift-validate`** — run before handoff; on P0/P1 findings, hand off to **`workflow-drift-guard`** (`.cursor/agents/workflow-drift-guard.md`).

Canonical detail: **`.local/index-and-planning/current/plan.md`** section **Implementer slice closure (mandatory end-of-loop)**.

## File retention policy (explicit)

- **Do not delete** workflow sources: `.agents/skills/**`, versioned `.cursor/rules`, `.cursor/agents`, `.cursor/skills` (see `.gitignore` exceptions), tracked `.ai_infra/scripts/pr/**`, or this checklist.
- **Do delete** (when appropriate): merged **git branches** only, via `finalize.py` / GitHub auto-delete — not markdown artifacts you still need for history (archive in `docs/archive/` instead if superseded).

## Canonical copies (avoid drift)

- Procedures + dedup rules: **`agent-workflow-procedures.md`**
- Skill order + finalization: **`.agents/skills/pr-workflow/SKILL.md`**
- Prepare gate list: **`.ai_infra/scripts/pr/prepare.py`** (`GATES`)
- CI shape: **`.github/workflows/kit-quality.yml`**

If this file and `pr-workflow/SKILL.md` or `prepare.py` disagree, **fix this file** to match the script/workflow truth.
