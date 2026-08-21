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

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Fresh consumer after `/workflow-activate` + identity in `github.collaboration.yaml`
- Human pastes **Project URL + repo URL** after `gh` auth
- User asks for kit default shell (six views + Tier-1 columns)
- `board-bootstrap --check` FAILs views, Tier-1 columns, or empty README

## Non-negotiable

| Do | Do not |
|----|--------|
| **CONSENT GATE** before shell apply | Mutate shell without description + explicit proceed |
| Accept Project + repo URLs; propose YAML via `gh project view` / `field-list` | Write YAML without human confirm |
| Coach **TURN PROTOCOL** — one turn at a time | Dump “follow views-setup.md” and stop |
| Run `board-bootstrap --check` until exit 0 | Undocumented GraphQL view mutations |
| `--ensure-fields` / `--apply-readme` only after CONSENT | Invent field option ids without discovery |
| Smoke `create-from-template` | Claim ready while `--check` exit 5 |
| Browser MCP only when user asks | Open browser unprompted |

Click reference: [views-setup.md](../../.ai_infra/templates/project-board/views-setup.md) § Browser assist map.

## CONSENT GATE (mandatory — every first-run shell)

**Before** TURN PROTOCOL, `--ensure-fields`, `--apply-readme`, or any future `--apply-shell`, stop and ask **both** questions in one message. Do **not** proceed until answered.

### Q1 — Board description (README blurb)

Ask:

```text
What short description should appear on this Project board?
(Reply with 1–3 sentences for the Project README, or say "use template default".)
```

- Custom text → keep for `--apply-readme` body merge.
- `use template default` → `.ai_infra/templates/project-board/project-readme.md`.
- README already non-empty + keep → record; skip overwrite unless asked.

### Q2 — Proceed to create / coach the default shell?

Ask:

```text
May I proceed to set up the kit default Playground board shell on this Project
(six views + Tier-1 columns + README)? Reply "yes" or "no".
```

- **`yes`** → Entry check + TURN PROTOCOL (and/or approved CLI flags).
- **`no`** → stop. Offer day-to-day triage only if shell already green.
- Ambiguous → ask again. Never assume yes.

Print after answers:

```text
board-shell consent: description=custom|template|keep · proceed=yes|no
```

Only `proceed=yes` unlocks the rest of this skill.

## Entry

0. Run **CONSENT GATE**. If `proceed=no` → Exit with consent line only.
1. If board ids missing and human provided URLs: propose collaboration YAML, confirm, save. Print:

```text
board-onboard status: api=complete · shell=incomplete · views=ui-only · next=/board CONSENT+TURN
```

**Automation boundary:** API automates YAML, field defs, README. **UI required** for six views + Tier-1 column visibility (no public view mutation API).

2. `python3 -m agent_colony project status`
3. `python3 -m agent_colony project doctor`
4. Load schema: overlay `.local/user_settings/board-shell.schema.yaml` or template `.ai_infra/templates/project-board/board-shell.schema.yaml`
5. `python3 -m agent_colony project board-bootstrap --check`

## Loop

```text
CONSENT GATE → doctor → board-bootstrap --check → (gaps?) → TURN PROTOCOL → re-check → smoke → ready
```

Read FAIL lines literally. Empty README is a **separate** fix after consent — never call a view-missing FAIL “only README”.

### WARN vs FAIL

| Outcome | Typical cause | Coach action |
|---------|---------------|--------------|
| **FAIL** (exit non-zero) | Missing default Playground view; empty README | **TURN PROTOCOL** — one turn, re-check |
| **WARN** (exit 0) | Missing Tier-1 columns on primary views | Now **FAIL (exit 5)** — coach until green |
| **WARN** (exit 0) | Leftover `View N`; layout mismatch | Rename/columns until cleared |
| **PASS** | Six views + README + `--check` exit 0 | Smoke card → Pattern A |

### TURN PROTOCOL (mandatory when views FAIL)

**Required:** one concrete UI turn → wait for human `done` → re-check → next turn.

**Forbidden:** single dump of views-setup.md then wait forever.

**Default:** human clicks in GitHub UI; you coach one turn.

**Opt-in browser assist:** When user explicitly asks (e.g. “use cursor-ide-browser”), you may use browser MCP for **that turn only**. Stop on login/2FA/permission blockers. Targets: [views-setup.md](../../.ai_infra/templates/project-board/views-setup.md) § Browser assist map.

**Open:** Project URL from `project status`.

| Turn | Goal | Done when |
|------|------|-----------|
| A | Rename **View 1** → **Status board**; Board layout; Group by **Status**; Tier-1 columns | Human replies `done`; fewer FAILs |
| B | **+ New view** → Table → **Prioritized backlog** + Tier-1 columns | `done`; re-check |
| C | **+ New view** → Roadmap → **Roadmap** | `done`; re-check |
| D | **+ New view** → Table → **Bugs**; filter title `[BUG]` | `done`; re-check |
| E | **+ New view** → Table → **In review**; filter Status = In review | `done`; re-check |
| F | **+ New view** → Table → **My items**; filter Assignees = `@me` | `done`; re-check |
| G | README via `--apply-readme` or paste `project-readme.md` | README non-empty; re-check |
| H | Clear Tier-1 column FAILs on Status board / Prioritized backlog | `--check` exits **0** |

**Fast minimal path:** Turn A → Turn B → Turn G → Turn H if needed → exit **0**.

**Optional polish:** Group by Priority on Prioritized backlog — not a bootstrap gate.

Between every turn print:

```text
board-shell turn: A|B|C|D|E|F|G|H · waiting=human · next=<view or column>
```

Checklist: `.ai_infra/templates/project-board/views-checklist.md`. Canon clicks: [views-setup.md](../../.ai_infra/templates/project-board/views-setup.md).

### Optional automation (official API only)

```bash
python3 -m agent_colony project board-bootstrap --check --ensure-fields
python3 -m agent_colony project board-bootstrap --check --apply-readme
```

- `--ensure-fields`: create missing field definitions; print suggested YAML ids. Does **not** create views.
- `--apply-readme`: push templated README via `updateProjectV2` (opt-in).

Respect GraphQL quota / outbox — never retry-loop.

### Smoke card

```bash
python3 -m agent_colony project create-from-template \
  --title "[LIVE-SMOKE] board shell onboard" --template slice \
  --status ready --priority p2 --size xs --estimate 0.5 --agent board
python3 -m agent_colony project validate-item --last
```

## Customization

**Minimal 2-view:** copy `board-shell.schema.minimal.yaml` exemplar → `.local/user_settings/board-shell.schema.yaml`. Coach Turns A + B only. Re-check after each turn.

**Playground default (six views):** edit overlay only if team intentionally drops a view. **Unsafe:** remove Tier-1 fields or hide Priority on Prioritized backlog.

## Exit

```text
board-shell: minimum=pass|fail · recommended=N missing · schema=<path> · next=day-to-day Pattern A
```

Say **ready for agents** only when `board-bootstrap --check` exits **0**.

## Canon

- Schema: `.ai_infra/templates/project-board/board-shell.schema.yaml`
- Clicks: [views-setup.md](../../.ai_infra/templates/project-board/views-setup.md)
- Day-to-day: `.cursor/skills/board-ssot/SKILL.md`
- ADR-008: coach + check by default; browser MCP only when user asks
