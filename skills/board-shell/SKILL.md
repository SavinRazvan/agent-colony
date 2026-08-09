---
name: board-shell
description: First-run coach for Playground-parity board shell — schema check, human views, smoke card.
---
<!--
File: SKILL.md
Path: .cursor/skills/board-shell/SKILL.md
Role: Guided first-time Project board shell setup against board-shell.schema.yaml.
Used By:
 - .cursor/agents/board.md (first-run / shell mode)
Depends On:
 - .ai_infra/templates/project-board/board-shell.schema.yaml
 - .ai_infra/templates/project-board/views-setup.md
 - python -m agent_colony project board-bootstrap
Notes:
 - Consent gate is mandatory before shell apply (description + proceed).
 - Views: coach TURN PROTOCOL by default; browser MCP only when user asks; opt-in CLI when official APIs allow (ADR-008).
 - Do not call undocumented GraphQL view mutations.
-->

# Board shell

## When

- Fresh consumer after `/workflow-activate` + identity in `github.collaboration.yaml` (board ids may still be empty)
- Human pastes **Project URL + repo URL** after `gh` auth — help wire `project_ssot` / `default_repo` before shell check
- User asks to apply the **kit default** board shell (Playground parity: six views + Tier-1 columns)
- `board-bootstrap --check` FAILs missing default views or **FAILs** Tier-1 columns on Status board / Prioritized backlog / empty README

## Non-negotiable

| Do | Do not |
|----|--------|
| **CONSENT GATE** before any shell apply (below) | Create/mutate shell without description + explicit proceed |
| After `gh` auth, accept Project + repo URLs and propose YAML via `gh project view` / `field-list` | Write YAML without human confirm |
| Coach humans through TURN PROTOCOL (`views-setup.md` = click reference only) | Dump “follow views-setup.md” and stop; undocumented GraphQL view mutations |
| Run `board-bootstrap --check` until exit 0 (views + Tier-1 columns) | Mutate Insights / workflows / status updates without approval |
| Optional `--ensure-fields` / `--apply-readme` **only after** CONSENT GATE (no view-apply CLI; **`--apply-shell` is not shipped**) | Invent field option ids into YAML without discovery |
| Smoke `create-from-template` | Claim “ready” while `--check` exit 5 or Prioritized backlog lacks **Priority** |
| Default: coach TURN PROTOCOL (human clicks); **if user asks** for browser help on views/columns → use **browser MCP** / cursor-ide-browser for that turn | Open browser MCP unprompted; multi-view instruction dumps; undocumented GraphQL view mutations |

## CONSENT GATE (mandatory — every first-run shell) 

**Before** TURN PROTOCOL, `--ensure-fields`, `--apply-readme`, or any future `--apply-shell`, stop and ask the human **both** questions in one message. Do **not** proceed until answered.

### Q1 — Board description (README blurb)

Ask:

```text
What short description should appear on this Project board?
(Reply with 1–3 sentences for the Project README, or say "use template default".)
```

- If they give text → keep it for README placeholders / `--apply-readme` body merge.
- If `use template default` → use `.ai_infra/templates/project-board/project-readme.md` as-is (board brief; title/repo filled from YAML).
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
1. If board ids missing and human provided URLs: propose collaboration YAML, confirm, save. After wire, print:

```text
board-onboard status: api=complete · shell=incomplete · views=ui-only · next=/board CONSENT+TURN
```

**Automation boundary:** API automates YAML, field defs, README; **UI required** for six views + Tier-1 column visibility (GitHub has no public view mutation API).

2. `python3 -m agent_colony project status`
3. `python3 -m agent_colony project doctor`
4. Load desired state:
   - Overlay if present: `.local/user_settings/board-shell.schema.yaml`
   - Else: `.ai_infra/templates/project-board/board-shell.schema.yaml`
5. `python3 -m agent_colony project board-bootstrap --check`

## Loop (refuse ready until default shell passes)

```text
CONSENT GATE → doctor → board-bootstrap --check → (gaps?) → TURN PROTOCOL → re-check → smoke → ready
```

**Read FAIL lines literally:** `FAIL — missing minimum view 'Status board'` (etc.) / `WARN — rename default view 'View 1'` → human UI until official apply CLI ships. Empty README / `--apply-readme` is a **separate** fix after consent — never tell the user a view-missing FAIL is “only README”.

### WARN vs FAIL (schema check)

| Outcome | Typical cause | Coach action |
|---------|---------------|--------------|
| **FAIL** (exit non-zero) | Missing a **default** Playground view; empty README | Enter **TURN PROTOCOL** below — do not stop after one sentence |
| **WARN** (exit 0) | Missing Tier-1 **columns** on primary views | Now **FAIL (exit 5)** — coach Turn H until green |
| **WARN** (exit 0) | Leftover `View N`; layout mismatch | Coach rename/columns until cleared |
| **PASS** | Six views + README + `board-bootstrap --check` exit 0 | Smoke card → day-to-day Pattern A |

### TURN PROTOCOL (mandatory when views FAIL) — do not skip

You **must** run this conversation loop. **Forbidden:** “follow views-setup.md”, “rename View 1”, or “add columns” as a single dump then waiting forever. **Required:** one concrete UI turn, wait for human “done”, then next turn.

**Default:** human performs clicks in GitHub UI; you coach one turn at a time.

**Opt-in browser assist:** If the user **explicitly** asks you to open the browser / use browser MCP / click views or columns for them (e.g. “help me in the browser”, “do Turn H for me”, “use cursor-ide-browser”), you **may** use **browser MCP** / cursor-ide-browser for **that** turn only. Still one turn → re-check → next. Do **not** open the browser unprompted. Stop and hand back to the human on login/2FA/permission blockers. Follow **Browser assist map** below (same targets as `views-setup.md`).

**Open:** Project URL from `project status` (e.g. `https://github.com/users/…/projects/N`).

### Browser assist map (universal click targets — opt-in only)

Use this when driving **cursor-ide-browser** (or when coaching clicks). Prefer **minimal 2-view** path unless the user asked for six-view Playground. After each turn: `board-bootstrap --check`.

| Goal | Where to go (GitHub Project UI) | Done when |
|------|----------------------------------|-----------|
| Open project | Navigate to Project URL from `project status` | Project header + view tabs visible |
| Select a view | Click the **view tab** by exact name (`Status board`, `Prioritized backlog`, …) | That view is active |
| Rename view | Active tab → **⋯** (or right-click / View menu) → **Rename** → type kit name → confirm | Tab label matches schema |
| New view | **+ New view** (or **New view**) → pick layout → name it | New tab exists with correct name |
| Layout | View menu / **⋯** → **Layout** → **Board** / **Table** / **Roadmap** | Layout matches turn |
| Group by (required) | View menu / toolbar **Group by** → **Status** (Status board) | Board columns are Status groups |
| Show Tier-1 columns | Active view → **+** / field picker / **Fields** / **View settings → Fields** → enable **Priority**, **Size**, **Estimate**, **Start date** | `--check` no longer FAILs those columns on that view |
| Clear Slice by (if set by mistake) | View menu → **Slice by** → **No slicing** (or clear) | No slice chips; groups only if Group by set |
| Save view | If UI shows unsaved / **Save** on the view | Changes persist after reload |
| README | Prefer CLI `--apply-readme` after consent; else Project **⋯** / Settings → **README** | README non-empty; `--check` OK |

**Fast minimal path (browser):** Turn A (Status board rename/layout/Group by Status + Tier-1 fields) → Turn B (Prioritized backlog Table + Tier-1 fields) → Turn G (README) → Turn H only if `--check` still FAILs columns → exit when `--check` **0**.

**Optional polish (not a bootstrap gate):** on **Prioritized backlog** → **Group by** → **Priority** (P0/P1/P2 sections). Empty boards may hide empty group headers until cards have Priority set. Do **not** block “ready for agents” on this.

**Browser stop conditions:** login / 2FA / permission / CAPTCHA / “can’t find control after 2 tries” → hand back to human with the same turn table row; do not invent GraphQL view mutations.

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
python3 -m agent_colony project board-bootstrap --check --apply-readme
```

Or paste contents of `project-readme.md` into Project README settings. Re-check.

**Turn H — clear Tier-1 column FAILs**

If `--check` still FAILs missing Priority/Size/Estimate/Start date on Status board or Prioritized backlog: open that view → **+** field picker → show the missing columns. Re-check until `board-bootstrap --check` exits **0** (no view FAIL and no Tier-1 column FAILs). Leftover `View N` WARNs are cosmetic and can be cleared separately.

Between every turn print:

```text
board-shell turn: A|B|C|D|E|F|G|H · waiting=human · next=<view or column>
```

Use checklist: `.ai_infra/templates/project-board/views-checklist.md`. Canon clicks: `.ai_infra/templates/project-board/views-setup.md`.

### Optional automation (official API only)

```bash
python3 -m agent_colony project board-bootstrap --check --ensure-fields
python3 -m agent_colony project board-bootstrap --check --apply-readme
```

- `--ensure-fields`: create missing **field definitions** by name; print suggested YAML field ids (human confirms before editing collaboration.yaml). Does **not** create views.
- `--apply-readme`: push templated README via `updateProjectV2` (opt-in; user approval).

Respect GraphQL quota / outbox — never retry-loop.

### Smoke card (prove Tier-1)

```bash
python3 -m agent_colony project create-from-template \
  --title "[LIVE-SMOKE] board shell onboard" --template slice \
  --status ready --priority p2 --size xs --estimate 0.5 --agent board
python3 -m agent_colony project validate-item --last
# cleanup: delete smoke item or set Done with Notes "smoke cleanup"
```

## Customization

### Minimal 2-view overlay

When the user asks for a **simple board** (Status board + Prioritized backlog only):

1. Explain: agent runtime uses CLI/API fields — extra Playground views are optional human UI.
2. Offer copy from `.ai_infra/templates/user-settings/exemplars/board-shell.schema.minimal.yaml` → `.local/user_settings/board-shell.schema.yaml`.
3. Coach **Turn A** (Status board) + **Turn B** (Prioritized backlog) only — skip Turns C–F. Optional: **Group by Priority** on Prioritized backlog (polish; not a `--check` gate).
4. Re-run `board-bootstrap --check` after each turn until exit **0**.

### Playground default (six views)

- Edit overlay `.local/user_settings/board-shell.schema.yaml` only if your team intentionally drops a Playground view (expect FAIL→WARN tradeoffs).
- **Safe:** Insights, Iteration columns, filters. (End date is Tier-1 — keep visible on Status board / Prioritized backlog.)
- **Unsafe:** remove Status / Priority / Size / Estimate / Start date fields, or hide **Priority** on Prioritized backlog.

## Exit

Print:

```text
board-shell: minimum=pass|fail · recommended=N missing · schema=<path> · next=day-to-day Pattern A
```

Only say **ready for agents** when `board-bootstrap --check` exits **0** (no view FAIL, no Tier-1 column FAIL on Status board / Prioritized backlog, README non-empty).

## Canon

- Schema: `.ai_infra/templates/project-board/board-shell.schema.yaml`
- Click map: `.ai_infra/templates/project-board/views-setup.md` § Browser assist map
- Day-to-day cards: `.cursor/skills/board-ssot/SKILL.md`
- ADR-008: no view API; coach + check by default; browser MCP only when user asks
