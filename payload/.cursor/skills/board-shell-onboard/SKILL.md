---
name: board-shell-onboard
description: First-run coach for Playground-parity board shell — schema check, human views, smoke card.
---
<!--
File: SKILL.md
Path: .cursor/skills/board-shell-onboard/SKILL.md
Role: Guided first-time Project board shell setup against board-shell.schema.yaml.
Used By:
 - .cursor/agents/project-board.md (first-run / shell mode)
Depends On:
 - .ai_infra/templates/project-board/board-shell.schema.yaml
 - .ai_infra/templates/project-board/views-setup.md
 - python -m cursor_workflow project board-bootstrap
Notes:
 - Views remain human UI (ADR-008). Do not call undocumented view APIs.
-->

# Board shell onboard (first-run coach)

## When

- Fresh consumer after `/workflow-activate` + `github.collaboration.yaml` wired
- User asks to make the board look like Playground (Status board, Prioritized backlog, …)
- `board-bootstrap --check` WARNs on `View N` / missing columns / empty README

## Non-negotiable

| Do | Do not |
|----|--------|
| Coach humans through `views-setup.md` | Create/rename/delete Project **views** via API |
| Run `board-bootstrap --check` until minimum green | Mutate Insights / workflows / status updates |
| Optional `--ensure-fields` / `--apply-readme` (Slice B) | Invent field option ids into YAML without discovery |
| Smoke `create-from-template` | Claim “ready” while minimum schema check fails |

## Entry

1. `python3 -m cursor_workflow project status`
2. `python3 -m cursor_workflow project doctor`
3. Load desired state:
   - Overlay if present: `.local/user_settings/board-shell.schema.yaml`
   - Else: `.ai_infra/templates/project-board/board-shell.schema.yaml`
4. `python3 -m cursor_workflow project board-bootstrap --check`

## Loop (refuse ready until minimum passes)

```text
doctor → board-bootstrap --check → (gaps?) → human paste pack → re-check → smoke card → ready
```

### Gaps → human paste pack

1. Open Project settings in GitHub UI.
2. **Follow** `.ai_infra/templates/project-board/views-setup.md` (do not paste that file into README).
3. Rename `View 1` → **Status board**, default table → **Prioritized backlog**.
4. Add Tier-1 columns: Priority, Size, Estimate, Start date.
5. Paste **contents of** `project-readme.md` into Project README (edit placeholders).
6. Optional recommended views: Roadmap, Bugs, In review, My items.
7. Checklist: `views-checklist.md`.
8. Re-run `board-bootstrap --check`.

### Optional automation (official API only)

```bash
python3 -m cursor_workflow project board-bootstrap --check --ensure-fields
python3 -m cursor_workflow project board-bootstrap --check --apply-readme
```

- `--ensure-fields`: create missing **field definitions** by name; print suggested YAML field ids (human confirms before editing collaboration.yaml).
- `--apply-readme`: push templated README via `updateProjectV2` (opt-in; user approval).

Respect GraphQL quota / outbox — never retry-loop.

### Smoke card (prove Tier-1)

```bash
python3 -m cursor_workflow project create-from-template \
  --title "[LIVE-SMOKE] board shell onboard" --template slice \
  --status ready --priority p2 --size xs --estimate 0.5 --agent project-board
python3 -m cursor_workflow project validate-item --last
# cleanup: delete smoke item or set Done with Notes "smoke cleanup"
```

## Customization

- Edit overlay `.local/user_settings/board-shell.schema.yaml` to rename desired views or drop recommended ones.
- **Safe:** customize recommended views / Insights.
- **Unsafe:** remove Status / Priority / Size / Estimate / Start date fields agents write.

## Exit

Print:

```text
board-shell: minimum=pass|fail · recommended=N missing · schema=<path> · next=day-to-day Pattern A
```

Only say **ready for agents** when `--check` has no minimum-view **FAIL** and README is non-empty.

## Canon

- Schema: `.ai_infra/templates/project-board/board-shell.schema.yaml`
- Day-to-day cards: `.cursor/skills/project-board-ssot/SKILL.md`
- ADR-008 human-only views (coach + check are allowed; view mutation is not)
