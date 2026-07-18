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
| `project-readme.md` | **Humans** | Copy into Project settings → README (GitHub UI). Do **not** paste into a terminal. |

Card bodies always include `## Acceptance`, `## Rollback`, and `## Notes` so `validate-item` and Entry/Exit stay consistent.

**Do not** paste Project settings labels (`Project name`, `Short description`, `README`, …) into bash — use `cursor_workflow project` recipes instead.

**Safe agent flow (token-efficient):**

```bash
python3 -m cursor_workflow project guide --agent implementer
python3 -m cursor_workflow project create-from-template --title "[SLICE] short-name" --template slice --status ready
python3 -m cursor_workflow project claim --last --agent implementer
python3 -m cursor_workflow project handoff --last --agent implementer --next verifier --to in_review
```

`--last` reads `.local/generated-data/project-last-item.json` (machine-local pointer, not a second Status SSOT).
