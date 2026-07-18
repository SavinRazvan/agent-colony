# ADR-008: GitHub Project board as agent SSOT

**Status:** accepted — **product doctrine for this repository** (`mas-workflow-kit-project-ssot`)  
**Date:** 2026-07-17 · **STANDALONE:** 2026-07-18

## Context

Classic MAS Workflow Kit used local markdown trackers under `.local/index-and-planning/current/` as session SSOT. Collaborators cannot share that state. **This repository is the product** — already separated from upstream `mas-workflow-kit` — and configures a GitHub Project in `.local/user_settings/github.collaboration.yaml` → `project_ssot`, driven via `python3 -m cursor_workflow project`. Local artifacts remain for PR gates, audits, and evidence.

Related: [ADR-006](ADR-006-agent-integration-model.md), [HANDOFF.md](../../../HANDOFF.md).

## Decision

1. **Only writable SSOT:** when `project_ssot.enabled: true` and `sync_policy: board_only`, the GitHub Project is the **only writable** coordination SSOT for backlog, Status, and multi-agent continuation. Agents must not dual-write competing slice status to `work-tracker.md` / `session-pointer.md`.
2. **`board_only` wins** — dual-mirror (local trackers + board both writable) is rejected; it causes worse agent drift (DRIFT-009).
3. **Offline fallback:** if enabled is false or `gh`/Projects unavailable, use `fallback: local_trackers` with an explicit warning — then resume board sync; never silent dual-write.
4. **Read-only exports:** optional snapshots (`project export`) may cache board state for audits/ICC later; they **must not** write Status and must never become a competing SSOT.
5. **Config habit:** board identity and field ids live next to `owner` in `github.collaboration.yaml` (not a separate primary settings file).
6. **Tooling:** Pattern A CLI (`cursor_workflow project`) wrapping `gh project`; MCP optional later.
7. **Item kind:** default DraftIssue; promote to Issue when linking PRs (`promote_to_issue_on_pr`).
8. **`project-board` agent:** independent-governed helper; not in PR pipelines. **All agents** Anchor on `project_ssot` when enabled: **Entry reads** the Project; **Exit updates** Status (and Notes) so work stays indexed for the next agent (continuation contract in `project-board-ssot` skill).
9. **Post-merge card close:** Pattern A (`merge.py` + project CLI) sets Status → Done and appends Notes (PR URL + SHA) — **not** a dedicated post-merge agent.
10. **Permanent decoupling (STANDALONE):** this repo is the board-SSOT product. Do **not** merge doctrine into upstream `mas-workflow-kit`. Upstream is historical lineage only.
11. **Human-only Project surfaces:** views, workflows, Insights, Project README, status updates, Ready prioritization / product roadmap — agents never edit these.
12. **Multi-collaborator attribution:** card Notes use `@owner.github_user/<agent>` (from each person’s `github.collaboration.yaml`). CLI: `append-notes --agent <name>` when `require_attribution_on_exit`. GitHub Assignees are humans only (`set-assignee`); agent role lives in Notes. Handoff: `next=@user/agent`.
13. **Board Pattern A recipes:** lifecycle actions are one CLI command each — `create-from-template`, `claim`, `handoff`, `validate-item`, `doctor` — wrapping atomics. Prefer recipes over multi-step shell. Exit codes: `0` ok; `2` usage/config; `3` gh/network; `4` not found; `5` validation. Card body templates live under `.ai_infra/templates/project-board/`. Project README/settings remain human-only (paste `project-readme.md` in the UI — never into a shell).

## Consequences

- New CLI module: `.ai_infra/install/cursor_workflow/project_cli.py`
- Skill: `.cursor/skills/project-board-ssot/SKILL.md` (Continuation contract + per-agent rights)
- Ops: `.ai_infra/docs/operations/project-board-collaboration.md`
- Agent: `.cursor/agents/project-board.md`
- Drift: DRIFT-009 (dual-write) and DRIFT-010 (board vs PRs / stale In progress; read-only export); workflow-drift-guard **reads and updates** the board on Exit
- Post-merge Done: Pattern A `merge.py` (not a dedicated agent)
- DraftIssue body edits: `append-notes` / `edit_item_body` resolve project item `PVTI_…` → content `DI_…` (+ preserve `--title`); Status/field edits stay on `PVTI_…`
- Attribution: `append-notes --agent` prefixes `@github_user/agent`; `merge.py` Notes use `@user/merge.py`; `set-assignee` for human My items (Issue-backed)
- Board Pattern A recipes + templates + structured `CODE=` exit lines; atomics remain for power use

## References

- `.local/user_settings/github.collaboration.yaml`
- Board: https://github.com/users/SavinRazvan/projects/3
