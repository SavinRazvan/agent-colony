<!--
  Human paste pack — Project settings → README (GitHub UI only).
  Board brief: what this Project is, who operates it, how Status moves.
  CLI cheat sheets belong in `project guide` and project-board-collaboration.md — not here.
  Do not paste this into a shell. Prefer `board-bootstrap --check --apply-readme` after edit.
-->

<!-- PROJECT_TITLE: Your Board Name (board SSOT) -->
# Your Board Name (board SSOT)

**Agent Colony** coordination board for <!-- DEFAULT_REPO: owner/repo --> `owner/repo`.

When Project SSOT is on (`project_ssot.enabled` + `sync_policy: board_only`), this Project is the **only writable** place for backlog and Status. Chat executes work; it is not the Status source of truth. Local `.local/` holds evidence (gates, audits) — not a second Status writer.

## Who operates this board

| Who | Owns |
|-----|------|
| **Humans** | Views, workflows, Insights, this README, Ready ordering / roadmap, status updates in the UI |
| **Agents** (Cursor + `agent_colony project`) | Claim cards, update Status + Notes, Tier-1 fields on cards they touch, handoffs |

Agents never paste this README into a shell. Day-to-day commands live in the app repo: `python3 -m agent_colony project guide` and `.ai_infra/docs/operations/project-board-collaboration.md`.

## How work moves

- Status: **Ready → In progress → In review → Done**
- Card body (Acceptance / Rollback / Notes) = continuation between agents — not chat alone
- Notes: `@github_user/agent · UTC · text`
- Agents set Priority / Size / Estimate (points), Assignee on Issue create, Start date on first In progress; open PRs via `mention-pr`. They do **not** set Iteration, Labels, Reviewers, or End date by default.

## Links

| | |
|--|--|
| **App repo** | `owner/repo` |
| **Agents guide** | `AGENTS.md` in the app (after `/workflow-activate`) |
| **Board ops + CLI** | `.ai_infra/docs/operations/project-board-collaboration.md` |
| **First-run views** | `.ai_infra/templates/project-board/views-setup.md` (follow in UI — do not paste here) |

## Default repo

`project_ssot.default_repo` in `.local/user_settings/github.collaboration.yaml` must match the app repo above.
