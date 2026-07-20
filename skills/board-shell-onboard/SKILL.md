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
- User asks to apply the **kit default** board shell (Playground parity: six views + Tier-1 columns)
- `board-bootstrap --check` FAILs missing default views or WARNs on missing **Priority** / Size / Estimate / Start date / empty README

## Non-negotiable

| Do | Do not |
|----|--------|
| Coach humans through `views-setup.md` against `board-shell.schema.yaml` | Create/rename/delete Project **views** via API |
| Run `board-bootstrap --check` until default views green + Tier-1 column WARNs gone | Mutate Insights / workflows / status updates |
| Optional `--ensure-fields` / `--apply-readme` | Invent field option ids into YAML without discovery |
| Smoke `create-from-template` | Claim “ready” while default schema check fails or Prioritized backlog lacks **Priority** |

## Entry

1. `python3 -m cursor_workflow project status`
2. `python3 -m cursor_workflow project doctor`
3. Load desired state:
   - Overlay if present: `.local/user_settings/board-shell.schema.yaml`
   - Else: `.ai_infra/templates/project-board/board-shell.schema.yaml`
4. `python3 -m cursor_workflow project board-bootstrap --check`

## Loop (refuse ready until default shell passes)

```text
doctor → board-bootstrap --check → (gaps?) → human paste pack → re-check → smoke card → ready
```

### WARN vs FAIL (schema check)

| Outcome | Typical cause | Coach action |
|---------|---------------|--------------|
| **FAIL** (exit non-zero) | Missing a **default** Playground view (Status board, Prioritized backlog, Roadmap, Bugs, In review, My items); empty README | Block “ready”; human completes `views-setup.md` / README |
| **WARN** (exit 0) | Missing Tier-1 **columns** (esp. **Priority** on Prioritized backlog); leftover `View N` name | Still coach columns; **do not** declare ready while Priority/Size/Estimate/Start date WARNs remain |
| **PASS** | All default views present; README non-empty; no Tier-1 column WARNs | Smoke card → day-to-day Pattern A |

### Gaps → human paste pack

1. Open Project settings in GitHub UI.
2. **Follow** `.ai_infra/templates/project-board/views-setup.md` (do not paste that file into README).
3. Create/rename until all **six default** views exist (see checklist).
4. On **Prioritized backlog** and **Status board**, show columns: Priority, Size, Estimate, Start date (plus Title, Assignees, Status, Linked pull requests).
5. Paste **contents of** `project-readme.md` into Project README (edit placeholders).
6. Checklist: `views-checklist.md`.
7. Re-run `board-bootstrap --check`.

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

- Edit overlay `.local/user_settings/board-shell.schema.yaml` only if your team intentionally drops a Playground view (expect FAIL→WARN tradeoffs).
- **Safe:** Insights, Iteration/End date columns, filters.
- **Unsafe:** remove Status / Priority / Size / Estimate / Start date fields, or hide **Priority** on Prioritized backlog.

## Exit

Print:

```text
board-shell: minimum=pass|fail · recommended=N missing · schema=<path> · next=day-to-day Pattern A
```

Only say **ready for agents** when `--check` has no default-view **FAIL**, README is non-empty, and Tier-1 column WARNs (Priority / Size / Estimate / Start date) are cleared.

## Canon

- Schema: `.ai_infra/templates/project-board/board-shell.schema.yaml`
- Day-to-day cards: `.cursor/skills/project-board-ssot/SKILL.md`
- ADR-008 human-only views (coach + check are allowed; view mutation is not)
