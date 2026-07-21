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
 - Consent gate is mandatory before shell apply (description + proceed).
 - Views: coach TURN PROTOCOL today; opt-in CLI when official APIs allow (ADR-008).
 - Do not call undocumented GraphQL view mutations.
-->

# Board shell onboard (first-run coach)

## When

- Fresh consumer after `/workflow-activate` + identity in `github.collaboration.yaml` (board ids may still be empty)
- Human pastes **Project URL + repo URL** after `gh` auth — help wire `project_ssot` / `default_repo` before shell check
- User asks to apply the **kit default** board shell (Playground parity: six views + Tier-1 columns)
- `board-bootstrap --check` FAILs missing default views or WARNs on missing **Priority** / Size / Estimate / Start date / empty README

## Non-negotiable

| Do | Do not |
|----|--------|
| **CONSENT GATE** before any shell apply (below) | Create/mutate shell without description + explicit proceed |
| After `gh` auth, accept Project + repo URLs and propose YAML via `gh project view` / `field-list` | Write YAML without human confirm |
| Coach humans through TURN PROTOCOL (`views-setup.md` = click reference only) | Dump “follow views-setup.md” and stop; undocumented GraphQL view mutations |
| Run `board-bootstrap --check` until default views green + Tier-1 column WARNs gone | Mutate Insights / workflows / status updates without approval |
| Optional `--ensure-fields` / `--apply-readme` **only after** CONSENT GATE (no view-apply CLI; **`--apply-shell` is not shipped**) | Invent field option ids into YAML without discovery |
| Smoke `create-from-template` | Claim “ready” while default schema check fails or Prioritized backlog lacks **Priority** |

## CONSENT GATE (mandatory — every first-run shell) 

**Before** TURN PROTOCOL, `--ensure-fields`, `--apply-readme`, or any future `--apply-shell`, stop and ask the human **both** questions in one message. Do **not** proceed until answered.

### Q1 — Board description (README blurb)

Ask:

```text
What short description should appear on this Project board?
(Reply with 1–3 sentences for the Project README, or say "use template default".)
```

- If they give text → keep it for README placeholders / `--apply-readme` body merge.
- If `use template default` → use `.ai_infra/templates/project-board/project-readme.md` as-is (title/repo filled from YAML).
- If README already non-empty and they say keep it → record that; skip overwrite unless they ask.

### Q2 — Proceed to create / coach the default shell?

Ask:

```text
May I proceed to set up the kit default Playground board shell on this Project
(six views + Tier-1 columns + README)? Reply "yes" or "no".
```

- **`yes`** → continue Entry check + TURN PROTOCOL (and/or approved CLI flags).
- **`no`** → stop. Do not coach views, do not `--apply-readme` / `--ensure-fields`. Offer day-to-day triage only if shell already green.
- Ambiguous reply → ask again. Never assume yes.

Print after answers:

```text
board-shell consent: description=custom|template|keep · proceed=yes|no
```

Only `proceed=yes` unlocks the rest of this skill.

## Entry

0. Run **CONSENT GATE** (Q1 + Q2). If `proceed=no` → Exit with consent line only.
1. If board ids missing and human provided URLs: propose collaboration YAML, confirm, save.
2. `python3 -m cursor_workflow project status`
3. `python3 -m cursor_workflow project doctor`
4. Load desired state:
   - Overlay if present: `.local/user_settings/board-shell.schema.yaml`
   - Else: `.ai_infra/templates/project-board/board-shell.schema.yaml`
5. `python3 -m cursor_workflow project board-bootstrap --check`

## Loop (refuse ready until default shell passes)

```text
CONSENT GATE → doctor → board-bootstrap --check → (gaps?) → TURN PROTOCOL → re-check → smoke → ready
```

**Read FAIL lines literally:** `FAIL — missing minimum view 'Status board'` (etc.) / `WARN — rename default view 'View 1'` → human UI until official apply CLI ships. Empty README / `--apply-readme` is a **separate** fix after consent — never tell the user a view-missing FAIL is “only README”.

### WARN vs FAIL (schema check)

| Outcome | Typical cause | Coach action |
|---------|---------------|--------------|
| **FAIL** (exit non-zero) | Missing a **default** Playground view; empty README | Enter **TURN PROTOCOL** below — do not stop after one sentence |
| **WARN** (exit 0) | Missing Tier-1 **columns**; leftover `View N` | Coach columns on Status board + Prioritized backlog until WARN gone |
| **PASS** | Six views + README + no Tier-1 WARNs | Smoke card → day-to-day Pattern A |

### TURN PROTOCOL (mandatory when views FAIL) — do not skip

You **must** run this conversation loop. **Forbidden:** “follow views-setup.md”, “rename View 1”, or “add columns” as a single dump then waiting forever. **Required:** one concrete UI turn, wait for human “done”, then next turn.

**Open:** Project URL from `project status` (e.g. `https://github.com/users/…/projects/N`).

**Turn A — kill `View 1` → Status board**

1. Tell human: open the Project → click the view tab named **View 1** (or similar).
2. Rename it to **Status board**.
3. Layout = **Board**; Group by = **Status**.
4. Show fields/columns: Title, Assignees, Status, **Priority**, **Size**, **Estimate**, **Start date**, Linked pull requests.
5. Ask: reply `done` when Status board exists. Then re-run `--check` (expect fewer FAILs).

**Turn B — Prioritized backlog (new Table view)**

1. **+ New view** → Table → name **Prioritized backlog**.
2. Show same Tier-1 columns as Status board (**Priority** required).
3. Wait for `done` → re-check.

**Turn C — Roadmap**

1. **+ New view** → Roadmap layout → name **Roadmap**.
2. Wait for `done` → re-check.

**Turn D — Bugs**

1. **+ New view** → Table → name **Bugs** (emoji optional).
2. Filter: title contains `[BUG]`.
3. Wait for `done` → re-check.

**Turn E — In review**

1. **+ New view** → Table → name **In review**.
2. Filter: Status = **In review**.
3. Wait for `done` → re-check.

**Turn F — My items**

1. **+ New view** → Table → name **My items**.
2. Filter: Assignees = `@me`.
3. Wait for `done` → re-check.

**Turn G — README**

```bash
python3 -m cursor_workflow project board-bootstrap --check --apply-readme
```

Or paste contents of `project-readme.md` into Project README settings. Re-check.

**Turn H — clear column WARNs**

If `--check` still WARNs missing Priority/Size/Estimate/Start date on Status board or Prioritized backlog: open that view → **+** field picker → show the missing columns. Re-check until **no FAIL and no those WARNs**.

Between every turn print:

```text
board-shell turn: A|B|C|D|E|F|G|H · waiting=human · next=<view or column>
```

Use checklist: `.ai_infra/templates/project-board/views-checklist.md`. Canon clicks: `.ai_infra/templates/project-board/views-setup.md`.

### Optional automation (official API only)

```bash
python3 -m cursor_workflow project board-bootstrap --check --ensure-fields
python3 -m cursor_workflow project board-bootstrap --check --apply-readme
```

- `--ensure-fields`: create missing **field definitions** by name; print suggested YAML field ids (human confirms before editing collaboration.yaml). Does **not** create views.
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
