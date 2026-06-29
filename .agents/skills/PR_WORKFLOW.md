# PR workflow (maintainer)

**Implementer work** (trackers, slices) uses `.local/index-and-planning/current/*`, `.cursor/agents/implementer.md`, and `.cursor/rules/implementation-workflow-governance.mdc`. Slice closure: `.ai_infra/docs/operations/workflow-complete.md` §F.

This file is the **merge path** only: **review → prepare → merge** (skills under `.agents/skills/<name>/`).

## Order

1. `review-pr` — findings only; optional **`make drift-validate`** before review when trackers changed. When scope is architecture-impacting, run **`enterprise-auditor`** (`.cursor/agents/enterprise-auditor.md` + `.cursor/skills/enterprise-architecture-audit/SKILL.md`) and write alignment artifacts per `.cursor/rules/advisory-audit-alignment-enforcement.mdc`.
2. `prepare-pr` — fixes + `prepare.py` (runs `GATES` from `.ai_infra/scripts/pr/prepare.py`).
3. `merge-pr` — `merge.py` check, `gh pr merge`, finalize repo state.

Per-step detail: the matching `SKILL.md` files in this directory (keep them as the short checklist).

## After push (before merge)

- `python .ai_infra/scripts/pr/verify_publish.py --branch "$(git branch --show-current)"`
- `gh pr view --json number,url,headRefName,state` (fix upstream with `git branch --set-upstream-to=origin/<branch> <branch>` if needed)

## Gates (do not duplicate elsewhere)

Authoritative list: **`GATES` in `.ai_infra/scripts/pr/prepare.py`**. Add **`python .ai_infra/scripts/architecture/check_governance_consistency.py`** when changing governance, workflows, or tracked policy docs. For substantive application code in consumer projects, align with project CI coverage bar when defined.

## User settings (complete once at install)

Gitignored worksheets under **`.local/user_settings/`** drive attribution for commits and PRs:

| File | Purpose |
|------|---------|
| `github.collaboration.yaml` | Owner, commit trailers, PR pipelines, `gh pr` body template |
| `mcp.agents.yaml` | External MCP servers + agent mapping worksheet |

**Validate:** `python -m cursor_workflow contributors validate`  
**Show resolved values:** `python -m cursor_workflow contributors show`  
**Commit trailers:** `python -m cursor_workflow contributors commit-trailers` (append to commit messages)  
**PR body:** `python -m cursor_workflow contributors pr-body --summary "…" --pipeline default`

PR scripts (`review.py`, `prepare.py`, `merge.py`) read **`owner`** from YAML and build **`Agent/s`** by merging:

1. **Implementation agents** from `change-index.md` (Agent column) + `session-pointer.md` (Last/Next agent)
2. **PR phase agents** from the selected `--pipeline` (`review-pr`, `prepare-pr`, `merge-pr`, …)

Default: **`--agents-from-session`** (use **`--no-agents-from-session`** for pipeline YAML only). Override anytime with explicit **`--agents "…"`**.

Inspect: `python -m cursor_workflow contributors show`

MCP tools (when `workflow_mcp` installed): `workflow_render_commit_trailers`, `workflow_render_pr_body`, `workflow_contributors_validate`.

## Artifacts (under `.local/`)

| Phase | Path |
|-------|------|
| Review | `workflow-artifacts/pr/review.md` |
| Prepare | `workflow-artifacts/pr/prep.md` |
| Merge | `workflow-artifacts/pr/merge.md` |
| Alignment (when required) | `workflow-artifacts/alignment/alignment-audit.md`, `alignment-todos.md` |

Attribution in each: `Action-By`, `GitHub-User`, `Agent/s` — resolved from **`.local/user_settings/github.collaboration.yaml`** when scripts run with `--pipeline` only (see **User settings** above). Fallback: `local_workflow_paths.DEFAULT_GITHUB_USER`.

## After merge (mandatory)

1. `git checkout main` && `git fetch --prune origin`
2. `python .ai_infra/scripts/pr/finalize.py --branch <feature-branch>` (optional: `--delete-merged-local`)
3. `git ls-remote --heads origin <feature-branch>` → empty
4. `git status --short --branch`

Optional: enable `delete_branch_on_merge` on the GitHub repo (`gh api repos/<owner>/<repo> -q .delete_branch_on_merge`).

## Hygiene

- Prefer **one** stacked PR from the tip branch when commits are strictly linear (avoids duplicate merges).
- Reject bypasses of project overlay rules / policy / tests. Doc updates for architecture-impacting PRs: `.ai_infra/docs/operations/documentation-maintenance-checklist.md` and indexes as needed.

## Git commit provenance (not PR artifacts)

- Complete **`.local/user_settings/github.collaboration.yaml`** once; render trailers with  
  `python -m cursor_workflow contributors commit-trailers` (or MCP `workflow_render_commit_trailers`).
- Policy: **`.cursor/rules/commit-trailer-format.mdc`** — required `Author` / `GitHub-User`; optional `Assisted-by:`; no `Made-with:`.
- Phase markdown uses `Action-By` / `GitHub-User` / `Agent/s` only; do not conflate with git trailers.

## Tracking when scope shifts

Update whatever actually changed among: `.local/index-and-planning/current/plan.md`, `work-tracker.md`, test trackers, project architecture docs.
