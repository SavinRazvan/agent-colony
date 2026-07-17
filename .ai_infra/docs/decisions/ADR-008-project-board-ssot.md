# ADR-008: GitHub Project board as agent SSOT

**Status:** accepted (experiment — this sibling repo only)  
**Date:** 2026-07-17

## Context

MAS Workflow Kit defaults to local markdown trackers under `.local/index-and-planning/current/` as session SSOT. Collaborators cannot share that state. This experiment (`mas-workflow-kit-project-ssot`) configures a GitHub Project in `.local/user_settings/github.collaboration.yaml` → `project_ssot` and drives it via `python -m cursor_workflow project`.

Related: [ADR-006](ADR-006-agent-integration-model.md), [HANDOFF.md](../../../HANDOFF.md).

## Decision

1. **`board_only` wins** when `project_ssot.enabled: true` and `sync_policy: board_only`. Agents must not dual-write competing slice status to `work-tracker.md` / `session-pointer.md`.
2. **Offline fallback:** if enabled is false or `gh`/Projects unavailable, use `fallback: local_trackers` with an explicit warning — then resume board sync; never silent dual-write.
3. **Config habit:** board identity and field ids live next to `owner` in `github.collaboration.yaml` (not a separate primary settings file).
4. **Tooling:** Pattern A CLI (`cursor_workflow project`) wrapping `gh project`; MCP optional later.
5. **Item kind:** default DraftIssue; promote to Issue when linking PRs (`promote_to_issue_on_pr`).
6. **`project-board` agent:** independent-governed helper; not in PR pipelines. Long-term all agents Anchor on `project_ssot`.
7. **Production port deferred** until demo + implementer Anchor + dual-write drift check + human sign-off. Marketplace kit stays markdown SSOT until then.

## Consequences

- New CLI module: `.ai_infra/install/cursor_workflow/project_cli.py`
- Skill: `.cursor/skills/project-board-ssot/SKILL.md`
- Agent: `.cursor/agents/project-board.md`
- Drift: DRIFT-009 advisory when board_only and tracker has competing `in_progress` (experiment)

## References

- `.local/user_settings/github.collaboration.yaml`
- Board: https://github.com/users/SavinRazvan/projects/3
