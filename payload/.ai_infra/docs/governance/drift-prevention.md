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
 - Last reviewed: 2026-06-29
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
2. Run **[documentation-maintenance-checklist.md](https://github.com/SavinRazvan/mas-workflow-kit/blob/main/.ai_infra/docs/operations/documentation-maintenance-checklist.md)** for kit doc surfaces.

## After changing `.local` layout

1. Update **`.ai_infra/docs/operations/local-workspace-layout.md`**.
2. Update **`.ai_infra/scripts/pr/local_workflow_paths.py`** (and `review.py` / `prepare.py` / `merge.py` consumers).
3. Refresh **`.ai_infra/templates/local-workspace/pages.json`** if dashboard tabs change.

## After changing **git commit** trailer policy

Follow **`agent-workflow-procedures.md` §3b**. Includes **`AGENTS.md`**, **`rules-overlap-matrix.md`**, **`workflow-source-owners.md`**, PR scripts, and mirrored `.cursor/` / `.agents/` skills. Run **`check_governance_consistency.py`** when tracked policy paths change.

## Operational drift (workflow-drift-guard)

Script-first checks for plan ↔ tracker ↔ session-pointer coherence and handoff doc parity. See [ADR-007](../decisions/ADR-007-workflow-drift-guard.md).

**Kit-dev PR prep:** `prepare.py` `resolve_gates()` auto-runs `drift validate` before merge (with doc facts). Optional: Task **`workflow-drift-guard`** after pass to refresh `.local/workflow-artifacts/drift/` artifacts.

| Concern | Owner | Do NOT duplicate in drift |
|---------|-------|---------------------------|
| Bare paths, brand terms | `check_governance_consistency.py`, `check_debrand.py` | Path/brand scans |
| Agent Anchor/MCP, registry parity | `integrate validate` INT-001…014 | Agent file structure |
| Canonical doc facts (roster, counts) | `check_doc_facts.py` / INT-013 | Path/brand scans |
| test-plan/index existence | `check_testing_artifacts.py` | File exists checks |
| Plugin/payload SHA drift | `sync_plugin_bundle.py --check` | Bundle sync |
| Slice claim verification | `verifier` | Subjective verification |
| Architecture scorecard | `enterprise-auditor` | Module deep-dive |

**Command:** `python -m cursor_workflow drift validate --directory .` or `make drift-validate`.

**Doc facts:** `python -m cursor_workflow doc validate --directory .` or `make doc-validate` (also in `make gates` and INT-013).

**Verify-all:** `make verify-all` — CI-aligned maintainer matrix with optional `--write-preflight`.

**Artifacts:** `.local/workflow-artifacts/drift/drift-audit.md`, `drift-todos.md`.

## Quarterly (or before kit releases)

- Confirm **`rules-overlap-matrix.md`** still lists all **`.cursor/rules/*.mdc`** files.
- Skim kit repo [**`IMPLEMENTATION-STATUS.md`**](https://github.com/SavinRazvan/mas-workflow-kit/blob/main/.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) vs shipped manifest profiles.
- Re-run **`make gates`**, **`make drift-validate`**, and **`make install-dry-run`** on the kit repo.
