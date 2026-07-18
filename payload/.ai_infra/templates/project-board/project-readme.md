# AI Project Playground (board SSOT)

This GitHub Project is the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only`.

| | |
|--|--|
| **Product repo** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot |
| **Handoff (agents)** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot/blob/main/HANDOFF.md |
| **Agents guide** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot/blob/main/AGENTS.md |
| **Board ops** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot/blob/main/.ai_infra/docs/operations/project-board-collaboration.md |

## What this board is for

- Shared backlog for humans and Cursor agents
- Status path: **Ready → In progress → In review → Done**
- Card body (Acceptance / Rollback / Notes) = continuation index — not chat alone
- Notes attributed as `@github_user/agent · UTC timestamp · text`
- **Tier-1 fields (agents):** claim may set **Start date** (UTC today); triage may set **Estimate** (`set-field --field estimate --to N`); open PR → `mention-pr --pr N` (Notes + derived Linked PRs). Agents do not set Iteration, Labels, Reviewers, or End date by default.

## Agents (CLI — never paste this README into a shell)

```bash
python3 -m cursor_workflow project doctor
python3 -m cursor_workflow project guide --agent implementer
python3 -m cursor_workflow project outbox status
python3 -m cursor_workflow project create-from-template --title "[SLICE] short-name" --template slice --status ready
python3 -m cursor_workflow project claim --last --agent implementer   # + Start date (UTC) when configured
python3 -m cursor_workflow project set-field --field estimate --to 3 --last
python3 -m cursor_workflow project mention-pr --pr <n> --last --agent implementer
python3 -m cursor_workflow project handoff --last --agent implementer --next verifier --to in_review
```

Use `--last` after create (saved under `.local/generated-data/project-last-item.json`). Do **not** invent or paste placeholder ids from docs.

If writes return EXIT_QUEUED (6) / rate-limit: `project outbox flush` after GraphQL quota recovers — do not retry in a loop.

## Humans only (this UI)

- Views, workflows, Insights, **this README**, status updates, Ready prioritization / product roadmap
- Paste updates here in the Project settings UI — do not run Project settings text as shell commands

## Default repo

`SavinRazvan/mas-workflow-kit-project-ssot` — see `project_ssot.default_repo` in collaboration YAML.
