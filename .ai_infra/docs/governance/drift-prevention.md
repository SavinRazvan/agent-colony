<!--
File: drift-prevention.md
Path: .ai_infra/docs/governance/drift-prevention.md
Role: Lightweight process to keep docs, `.local` layout docs, and script-first workflow aligned.
Used By:
 - .ai_infra/docs/governance/README.md
 - Maintainers after governance or workflow edits
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/scripts/architecture/check_governance_consistency.py
 - .ai_infra/docs/operations/documentation-maintenance-checklist.md
Notes:
 - Run governance consistency when changing rules, skills headers, or merge.py expectations.
 - Last reviewed: 2026-06-14
-->

# Drift prevention (lightweight)

## Default merge gates (canonical)

Order and commands: **`.ai_infra/scripts/pr/prepare.py`** (`GATES`) only — **do not list** commands here; run `prepare.py` or read that file.

Additionally when changing governance, workflows, `.cursor/`, `.agents/`, or tracked policy docs: **`python .ai_infra/scripts/architecture/check_governance_consistency.py`**.

## After changing workflow gates or artifact paths

1. Update **`.ai_infra/scripts/pr/prepare.py`** (`GATES`) if commands change.
2. Update **`.cursor/rules/pr-workflow-enforcement.mdc`** (short pointers only — no long gate lists in chat).
3. Update **`.ai_infra/docs/operations/workflow-complete.md`** and **`agent-workflow-procedures.md`** if checklist text references paths or commands.
4. Update **`README.md`** / **`AGENTS.md`** if onboarding paths change.
5. Run **`python .ai_infra/scripts/architecture/check_governance_consistency.py`** and targeted tests.

## After changing documentation lifecycle

1. Update **`.ai_infra/docs/governance/workflow-source-owners.md`** if ownership moved.
2. Run **[documentation-maintenance-checklist.md](../operations/documentation-maintenance-checklist.md)** for kit doc surfaces.

## After changing `.local` layout

1. Update **`.ai_infra/docs/operations/local-workspace-layout.md`**.
2. Update **`.ai_infra/scripts/pr/local_workflow_paths.py`** (and `review.py` / `prepare.py` / `merge.py` consumers).
3. Refresh **`.ai_infra/templates/local-workspace/pages.json`** if dashboard tabs change.

## After changing **git commit** trailer policy

Follow **`agent-workflow-procedures.md` §3b**. Includes **`AGENTS.md`**, **`rules-overlap-matrix.md`**, **`workflow-source-owners.md`**, PR scripts, and mirrored `.cursor/` / `.agents/` skills. Run **`check_governance_consistency.py`** when tracked policy paths change.

## Quarterly (or before kit releases)

- Confirm **`rules-overlap-matrix.md`** still lists all **`.cursor/rules/*.mdc`** files.
- Skim **`IMPLEMENTATION-STATUS.md`** vs shipped manifest profiles.
- Re-run **`make gates`** and **`make install-dry-run`** on the kit repo.
