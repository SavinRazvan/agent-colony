# AI Project Playground (board SSOT)

This GitHub Project is the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only` in each collaborator's `.local/user_settings/github.collaboration.yaml`.

## Agents (CLI — never paste this page into a shell)

```bash
python3 -m cursor_workflow project doctor
python3 -m cursor_workflow project list --status ready
python3 -m cursor_workflow project claim --id PVTI_… --agent implementer
python3 -m cursor_workflow project handoff --id PVTI_… --agent implementer --next verifier --to in_review
```

Notes are attributed as `@github_user/agent` (from `owner.github_user`).

## Humans only (this UI)

- Views, workflows, Insights, **this README**, status updates, Ready prioritization / product roadmap
- Paste updates here in the Project settings UI — do not run Project settings text as shell commands

## Status path

Ready → In progress → In review → Done

## Default repo

See `project_ssot.default_repo` in collaboration YAML (issues created from this project land there).
