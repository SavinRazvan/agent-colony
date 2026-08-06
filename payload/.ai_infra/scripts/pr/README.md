<!--
File: README.md
Path: .ai_infra/scripts/pr/README.md
Role: Hub for maintainer PR scripts and how they relate to git commit trailers vs `.local` artifacts.
Used By:
 - Maintainers, `.agents/skills/pr-workflow/SKILL.md`
Depends On:
 - .ai_infra/scripts/pr/local_workflow_paths.py
 - .ai_infra/scripts/pr/prepare.py
 - .cursor/rules/commit-trailer-format.mdc
 - .cursor/rules/pr-workflow-enforcement.mdc
Notes:
 - Gate order is canonical in prepare.py `resolve_gates()` (`GATES` = 2-gate back-compat alias).
-->

# PR workflow scripts (`.ai_infra/scripts/pr/`)

| Script | Role |
|--------|------|
| `review.py` | Stamp `review.md` under `.local/workflow-artifacts/pr/` |
| `prepare.py` | Run merge gates via `resolve_gates()` (`GATES` = 2-gate alias) and stamp `prep.md` |
| `merge.py` | Preconditions + stamp `merge.md` |
| `finalize.py` | Post-merge branch cleanup |
| `verify_publish.py` | Branch / origin-tracking sanity before merge workflow |
| `local_workflow_paths.py` | Canonical artifact paths (also referenced by rules) |

## Git commits vs PR markdown

- **Git** trailers live only in **commit messages**: **`.cursor/rules/commit-trailer-format.mdc`** — required **`Author:`** / **`GitHub-User:`**, optional **`Assisted-by:`**; **do not** use **`Made-with:`**. See **`AGENTS.md`** § Commits.
- **`review.md` / `prep.md` / `merge.md`** use **PR-phase** headers (`Action-By`, `Agent/s`, …). Scripts write those paths via **`local_workflow_paths.py`**; they are **not** git trailers.
