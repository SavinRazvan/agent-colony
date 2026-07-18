# AI Project Playground (board SSOT)

This GitHub Project is the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only`.

## Agents (CLI — never paste this page into a shell)

```bash
python3 -m cursor_workflow project doctor
python3 -m cursor_workflow project guide --agent implementer
python3 -m cursor_workflow project outbox status
python3 -m cursor_workflow project create-from-template --title "[SLICE] short-name" --template slice --status ready
python3 -m cursor_workflow project claim --last --agent implementer
python3 -m cursor_workflow project handoff --last --agent implementer --next verifier --to in_review
```

Use `--last` after create (saved under `.local/generated-data/project-last-item.json`). Do **not** invent or paste placeholder ids from docs.

If writes return EXIT_QUEUED (6) / rate-limit: `project outbox flush` after GraphQL quota recovers — do not retry in a loop.
Notes are attributed and timestamped by CLI as `@github_user/agent · YYYY-MM-DDTHH:MM:SSZ · text` (from `owner.github_user`). Use `claim` / `handoff` / `append-notes --agent` — do not hand-forge times.

## Humans only (this UI)

- Views, workflows, Insights, **this README**, status updates, Ready prioritization / product roadmap
- Paste updates here in the Project settings UI — do not run Project settings text as shell commands

## Status path

Ready → In progress → In review → Done

## Default repo

See `project_ssot.default_repo` in collaboration YAML (issues created from this project land there).
