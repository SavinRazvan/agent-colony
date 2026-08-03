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
4. **Rate-limit outbox:** when GraphQL quota blocks writes, `project_ssot.outbox` stores structured ops in a local JSONL (`.local/generated-data/board-outbox.jsonl`). EXIT_QUEUED (6) is soft-success; `outbox flush` restores the board after reset. Outbox is **never** authoritative Status.
5. **Read-only exports:** optional snapshots (`project export`) may cache board state for audits/ICC later; they **must not** write Status and must never become a competing SSOT.
6. **Config habit:** board identity and field ids live next to `owner` in `github.collaboration.yaml` (not a separate primary settings file).
7. **Tooling:** Pattern A CLI (`cursor_workflow project`) wrapping `gh project`; MCP optional later.
8. **Item kind / promote:** `item_kind_default: issue|draft` — **issue is the product default** (`gh issue create` + `gh project item-add`) so Assignees + Linked PRs work from claim. `draft` is scratch-only (DraftIssue). CLI `project promote-to-issue` converts leftover Drafts (**same PVTI_**). `mention-pr` auto-promotes Draft when `promote_to_issue_on_pr` (default true). Claim does **not** auto-promote. Do not create shippable work as Draft.
9. **`board` agent:** independent-governed helper; not in PR pipelines. **All agents** Anchor on `project_ssot` when enabled: **Entry reads** the Project; **Exit updates** Status (and Notes) so work stays indexed for the next agent (continuation contract in `board-ssot` skill).
10. **Post-merge card close:** Pattern A (`merge.py` + project CLI) sets Status → Done and appends Notes (PR URL + SHA) — **not** a dedicated post-merge agent.
11. **Permanent decoupling (STANDALONE):** this repo is the board-SSOT product. Do **not** merge doctrine into upstream `mas-workflow-kit`. Upstream is historical lineage only.
12. **Human-owned Project surfaces (no view API):** views, workflows, Insights, status updates, Ready prioritization / product roadmap have **no official mutation API** for views/column visibility. **Desired-state schema** (`.ai_infra/templates/project-board/board-shell.schema.yaml`, optional overlay `.local/user_settings/board-shell.schema.yaml`) drives `project board-bootstrap --check` and the first-run coach (`.cursor/skills/board-shell/SKILL.md`) — check/coach by default; **no** view create/rename via GraphQL. Opt-in exceptions (explicit flags, user-approved): `board-bootstrap --ensure-fields` (create missing field **definitions**) and `board-bootstrap --apply-readme` (`updateProjectV2` README). **Browser MCP / cursor-ide-browser** for views/columns is allowed **only when the human explicitly asks** the agent to help in the browser (still one TURN PROTOCOL turn at a time; stop on login/2FA). Default remains human clicks + coach. Human paste-pack: `views-setup.md` / `views-checklist.md` / `project-readme.md`.
13. **Multi-collaborator attribution:** card Notes use `@owner.github_user/<agent> · <ISO-8601-UTC> · …` (from each person’s `github.collaboration.yaml`; CLI stamps UTC). CLI: `append-notes --agent <name>` when `require_attribution_on_exit`. GitHub Assignees are humans only (`set-assignee`); agent role lives in Notes. Handoff: `next=@user/agent`. Local `history/continuity-index.md` rolls ≥3 days; board Notes keep full card lifetime.
14. **Board Pattern A recipes:** lifecycle actions are one CLI command each — `create-from-template`, `claim`, `handoff`, `promote-to-issue`, `validate-item`, `doctor`, `queue`, `outbox status|flush` — wrapping atomics. Prefer recipes over multi-step shell. Exit codes: `0` ok; `2` usage/config; `3` gh/network; `4` not found; `5` validation; `6` queued. Card body templates live under `.ai_infra/templates/project-board/`. Project README/settings remain human-only (paste `project-readme.md` in the UI — never into a shell).
15. **Tier-1 board fields:** agents set **Priority/Size/Estimate** on create/own (Size↔Estimate **points** rubric in `board-ssot` skill). **Start date** (UTC) is set when Status becomes `in_progress` if empty — via `claim`, `set-status --to in_progress`, or `handoff --to in_progress` — when `conventions.set_start_date_on_claim` and `fields.start_date.field_id` are configured. PR linkage via `mention-pr --pr N`. **Out of scope for agents by default:** Iteration, Labels, Reviewers, End date (human / UI).

## Consequences

- New CLI module: `.ai_infra/install/cursor_workflow/project_cli.py` + `project_outbox.py`
- Skill: `.cursor/skills/board-ssot/SKILL.md` (Continuation contract + per-agent rights)
- Ops: `.ai_infra/docs/operations/project-board-collaboration.md`
- Agent: `.cursor/agents/board.md`
- Drift: DRIFT-009 (dual-write) and DRIFT-010 (board vs PRs / stale In progress; read-only export); DRIFT-004b (session Board vs snapshot); drift-guard **reads and updates** the board on Exit; pending outbox is not a DRIFT failure
- Post-merge Done: Pattern A `merge.py` (not a dedicated agent)
- DraftIssue body edits: `append-notes` / `edit_item_body` resolve project item `PVTI_…` → content `DI_…` (+ preserve `--title`); Status/field edits stay on `PVTI_…`
- Attribution: `append-notes --agent` prefixes `@github_user/agent · <ISO-8601-UTC> ·`; `merge.py` Notes use `@user/merge.py`; `set-assignee` for human My items (Issue-backed)
- Board Pattern A recipes + templates + structured `CODE=` exit lines; rate-limit outbox (`project_ssot.outbox`); atomics remain for power use
- Promote Draft→Issue: `project promote-to-issue` (GraphQL `convertProjectV2DraftIssueItemToIssue`; same `PVTI_`); `mention-pr` auto when `promote_to_issue_on_pr`

## References

- `.local/user_settings/github.collaboration.yaml`
- Board: https://github.com/users/SavinRazvan/projects/3
