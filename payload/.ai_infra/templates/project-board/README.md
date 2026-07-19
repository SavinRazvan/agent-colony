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
 - Project README / views / Insights are human-only (ADR-008); paste project-readme.md in the UI.
-->

# Project board templates

| File | Who | How |
|------|-----|-----|
| `card-body-slice.md` | Agents | `python3 -m cursor_workflow project create-from-template --template slice --title "…"` |
| `card-body-bug.md` | Agents | `create-from-template --template bug` |
| `card-body-research.md` | researcher / project-board | `create-from-template --template research` |
| `outbox-entry.schema.json` | Agents / CLI | Validate lines in `.local/generated-data/board-outbox.jsonl` |
| `outbox-entry.example.json` | Docs | Exemplar outbox line (never paste fake `item_id` as `--id`) |
| `project-readme.md` | **Humans** | Copy into Project settings → README (GitHub UI). Do **not** paste into a terminal. |

Card bodies always include `## Acceptance`, `## Rollback`, and `## Notes` so `validate-item` and Entry/Exit stay consistent.

**Notes format (CLI):** `@github_user/agent · YYYY-MM-DDTHH:MM:SSZ · text` — stamped by `claim`, `handoff`, and `append-notes --agent`. Do not hand-forge timestamps.

| Need | Template / action |
|------|-------------------|
| slice / feature work | `create-from-template --template slice` |
| bug fix | `create-from-template --template bug` |
| external / corpus research | `create-from-template --template research` |
| Project README | **Humans only** — paste `project-readme.md` in Project settings UI |

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

`--priority` is required on `create-from-template`. `--size`/`--estimate` default to `s`/`1` (Notes when guessed). Size↔Estimate points table: `project-board-ssot` skill. `--last` reads `.local/generated-data/project-last-item.json` (machine-local pointer, not a second Status SSOT). Claim does **not** auto-promote; `mention-pr` auto-promotes Draft when `promote_to_issue_on_pr` (default true). Start date sets on claim / first In progress when configured.

**Rate-limit outbox (do not hammer GraphQL):**

```bash
python3 -m cursor_workflow project outbox status
python3 -m cursor_workflow project queue --op append-notes --last --agent implementer --text "deferred note"
python3 -m cursor_workflow project outbox flush
```

When a write returns `EXIT_QUEUED` (6), continue local evidence (`change-index` / handoff line); flush after `gh api rate_limit` recovers. Outbox is **not** a second Status SSOT.
