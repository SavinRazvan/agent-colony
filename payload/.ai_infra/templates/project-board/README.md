<!--
File: README.md
Path: .ai_infra/templates/project-board/README.md
Role: Index for GitHub Project card / Project README templates (board Pattern A).
Used By:
 - .ai_infra/install/cursor_workflow/project_cli.py (create-from-template)
 - .cursor/skills/project-board-ssot/SKILL.md
Depends On:
 - conventions.body_sections in github.collaboration.yaml
Notes:
 - Never paste GitHub Project *settings UI* text into a shell — that is not a CLI.
 - Views stay human UI (ADR-008). Schema + board-bootstrap --check coach the shell;
   opt-in --ensure-fields / --apply-readme only.
-->

# Project board templates

| File | Who | How |
|------|-----|-----|
| `card-body-slice.md` | Agents | `create-from-template --template slice --title "…" --priority p1` (size/estimate default s/1) |
| `card-body-bug.md` | Agents | `create-from-template --template bug --priority p1` |
| `card-body-research.md` | researcher / project-board | `create-from-template --template research --priority p2` |
| `board-shell.schema.yaml` | Coach / CLI | Desired-state Playground parity; overlay `.local/user_settings/board-shell.schema.yaml` |
| `outbox-entry.schema.json` | Agents / CLI | Validate lines in `.local/generated-data/board-outbox.jsonl` |
| `outbox-entry.example.json` | Docs | Exemplar outbox line (never paste fake `item_id` as `--id`) |
| `project-readme.md` | **Humans** (or `--apply-readme`) | Paste **contents** into Project settings → README (edit placeholders). Do **not** paste into a terminal. |
| `views-setup.md` | **Humans** | **Follow** in GitHub UI (rename views / add columns). Do **not** paste this file into Project README. |
| `views-checklist.md` | **Humans** | Checkbox checklist for minimum + recommended views. |

Card bodies always include `## Acceptance`, `## Rollback`, and `## Notes` so `validate-item` and Entry/Exit stay consistent.

**Notes format (CLI):** `@github_user/agent · YYYY-MM-DDTHH:MM:SSZ · text` — stamped by `claim`, `handoff`, and `append-notes --agent`. Do not hand-forge timestamps.

| Need | Template / action |
|------|-------------------|
| slice / feature work | `create-from-template --template slice --priority p1` |
| bug fix | `create-from-template --template bug --priority p1` |
| external / corpus research | `create-from-template --template research --priority p2` |
| Project board bootstrap | `project doctor` → `/project-board` first-run (`board-shell-onboard`) → follow `views-setup.md` → paste `project-readme.md` → `project board-bootstrap --check` → `project status` |
| Project README | **Humans** paste **contents of** `project-readme.md`, or opt-in `board-bootstrap --check --apply-readme` |

**Do not** paste Project settings labels (`Project name`, `Short description`, `README`, …) into bash — use `cursor_workflow project` recipes instead.

**Safe agent flow (token-efficient):**

```bash
python3 -m cursor_workflow project guide --agent implementer
python3 -m cursor_workflow project create-from-template --title "[SLICE] short-name" --template slice --status ready --priority p1 --size s --estimate 1 --agent implementer
python3 -m cursor_workflow project claim --last --agent implementer
python3 -m cursor_workflow project promote-to-issue --last --agent implementer
python3 -m cursor_workflow project mention-pr --pr <n> --last --agent implementer
python3 -m cursor_workflow project handoff --last --agent implementer --next verifier --to in_review
```

`--priority` is required on `create-from-template`. `--size`/`--estimate` default to `s`/`1` (Notes when guessed). Issue create assigns `owner.github_user` unless `--no-assignee`. Size↔Estimate points table: `project-board-ssot` skill. `--last` reads `.local/generated-data/project-last-item.json` (machine-local pointer, not a second Status SSOT). Claim does **not** auto-promote; `mention-pr` auto-promotes Draft when `promote_to_issue_on_pr` (default true). Start date sets on claim / first In progress when configured.

**Rate-limit outbox (do not hammer GraphQL):**

```bash
python3 -m cursor_workflow project outbox status
python3 -m cursor_workflow project queue --op append-notes --last --agent implementer --text "deferred note"
python3 -m cursor_workflow project outbox flush
```

When a write returns `EXIT_QUEUED` (6) — including precheck low quota, rate-limit / 429 / Forbidden throttle — continue local evidence (`change-index` / handoff line); do **not** retry-loop; flush after `gh api rate_limit` recovers. Outbox is **not** a second Status SSOT. See `project_ssot.outbox` (`precheck_writes`, `dedupe_pending`) in the collaboration exemplar.
