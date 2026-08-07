<!--
  Human paste pack — Project settings → README (GitHub UI only).
  Edit placeholders below, then paste this file's contents into the Project README field.
  Do not paste this into a shell. Agents never mutate Project README (ADR-008).
-->

<!-- PROJECT_TITLE: Your Board Name (board SSOT) -->
# Your Board Name (board SSOT)

This GitHub Project is the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only`.

| | |
|--|--|
| **App / product repo** | <!-- DEFAULT_REPO: owner/repo --> `owner/repo` |
| **Agents guide** | `AGENTS.md` in the app repo (after `/workflow-activate`) |
| **Board ops** | `.ai_infra/docs/operations/project-board-collaboration.md` (kit install) |
| **Views setup** | Follow `.ai_infra/templates/project-board/views-setup.md` (do not paste that file here) |

## What this board is for

- Shared backlog for humans and Cursor agents
- Status path: **Ready → In progress → In review → Done**
- Card body (Acceptance / Rollback / Notes) = continuation index — not chat alone
- Notes attributed as `@github_user/agent · UTC timestamp · text`
- **Tier-1 fields (agents):** Priority/Size/Estimate on create (Size↔Estimate **points** table in kit skill); **Assignee** = human owner on Issue create; **Start date** (UTC) on first In progress via `claim` / `set-status` / `handoff --to in_progress`; promote Draft→Issue; open PR → `mention-pr`. Agents do not set Iteration, Labels, Reviewers, or End date by default.

## Agents (CLI — never paste this README into a shell)

```bash
python3 -m agent_colony project doctor
python3 -m agent_colony project board-bootstrap --check
python3 -m agent_colony project guide --agent implementer
python3 -m agent_colony project outbox status
python3 -m agent_colony project create-from-template --title "[SLICE] short-name" --template slice --status ready --priority p1 --size s --estimate 1 --agent implementer
python3 -m agent_colony project claim --last --agent implementer   # + Start date (UTC) when configured
python3 -m agent_colony project promote-to-issue --last --agent implementer   # Draft→Issue; same PVTI_; before PR if not using mention-pr auto
python3 -m agent_colony project mention-pr --pr <n> --last --agent implementer   # auto-promotes Draft when promote_to_issue_on_pr (default true)
python3 -m agent_colony project handoff --last --agent implementer --next verifier --to in_review
```

Use `--last` after create (saved under `.local/generated-data/project-last-item.json`). Do **not** invent or paste placeholder ids from docs.

If writes return EXIT_QUEUED (6) / rate-limit: `project outbox flush` after GraphQL quota recovers — do not retry in a loop.

## Humans only (this UI)

- Views, workflows, Insights, **this README**, status updates, Ready prioritization / product roadmap
- Standard shell first (`views-setup.md` minimum), then customize
- Paste updates here in the Project settings UI — do not run Project settings text as shell commands

## Default repo

Set `project_ssot.default_repo` in `.local/user_settings/github.collaboration.yaml` to match <!-- DEFAULT_REPO --> above.
