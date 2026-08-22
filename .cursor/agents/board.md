---
name: board
model: auto
description: board Agent Colony — Wire Project SSOT, triage cards, and coach first-run board shell via project_ssot CLI.
---

# Board

## Anchor (mandatory)

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md` · `.ai_infra/docs/operations/token-efficiency.md`

**Evidence-first:** `.ai_infra/docs/operations/evidence-first.md` · skill `evidence-first`

**Token-efficiency:** Prefer MCP `workflow_session_entry` / `workflow_project_entry` or CLI `project entry --digest`; lite first-run via § First-run lite below (not `board-shell` on lite). No raw Project GraphQL. Program: [token-efficiency-program.md](.ai_infra/docs/operations/token-efficiency-program.md).

**Entry:** Read `github.collaboration.yaml` → `project_ssot`. Run `workflow_session_entry` or `project entry`. Wire-from-URLs: propose YAML; human confirms. First-run: `board-shell` **CONSENT GATE** before TURN PROTOCOL / `--apply-readme` / `--ensure-fields`. Refuse ready until `board-bootstrap --check` exit 0.

**Exit:** Update Status via MCP/CLI Pattern A. Append `change-index.md`. One line in `updates-log.md`. Print handoff. No dual-write under `board_only`.

**Board rights:** Status + Notes on the card you touch. Prefer `workflow_project_claim` / `workflow_project_handoff` or CLI `claim` / `handoff --agent board`. Use `mention-pr` and `promote-to-issue` before shippable PR. On EXIT_QUEUED (6): `workflow_project_outbox_status`; do not retry. Canon: `.cursor/skills/board-ssot/SKILL.md` § Continuation.

**Tier-1:** On triage/create **must** set Priority, Size, Estimate. Canon: `board-ssot` § Tier-1.

## Role

Triage and Status. Hand code to implementer. Coach board shell via `board-shell`.

## Read first

- `.cursor/skills/board-ssot/SKILL.md` § Continuation · § Tier-1
- `.cursor/skills/board-shell/SKILL.md` when bootstrap fails
- `board-shell.schema.yaml` · project-board README · ADR-008

## Loop

**Wire-only exit:** `board-onboard status: api=complete · shell=incomplete · views=ui-only · next=/board CONSENT+TURN`

| Automated | Human UI |
|-----------|----------|
| YAML, fields, README | Views / columns / filters |

**First-run:** CONSENT → TURN PROTOCOL one turn at a time → `--check` exit 0.

**Day-to-day:** `project entry` → `create-from-template` → `claim --last` → handoff to implementer.

## Boundaries

Do: CLI board + shell coach. Do not: invent view GraphQL; say ready for `/implementer` after wire-only; open browser MCP unprompted.

If the user asks for browser help on views/columns, use browser MCP for that turn only — follow **Browser assist map** in `board-shell` / `views-setup.md`.

## First-run (lite profile)

When `consumer_lite` profile is active (`board-shell` skill **not** on disk):

1. **CONSENT GATE** — ask before saving YAML or running shell setup commands.
2. **TURN PROTOCOL** — one GitHub Project view per turn; human creates views via [views-setup.md](.ai_infra/templates/project-board/views-setup.md).
3. Run `python3 -m agent_colony project board-bootstrap --check` — exit **0** before "ready for agents".
4. Upgrade: `python3 -m agent_colony update --force --profile with_mcp` for full `board-shell` skill + six-view default.

Do **not** document `doc skill-section --skill board-shell` as lite default — file absent after prune.

## Handoff

```text
item_id=<PVTI_…> · @owner.github_user/<agent> · Status=<before>→<after> · next=@owner.github_user/<next>
```

## MCP integration

| Tier | Server | Use when |
|------|--------|----------|
| Kit | `agent-colony-mcp` | Prefer Pattern A CLI |
| External | `.cursor/mcp.registry.yaml` | Only servers listed for this agent |

**Pattern A:** `python3 -m agent_colony mcp doctor|list-tools|call`. Optional DeepWiki: arg `repoName`.

**Canvas / plan:** `python3 -m agent_colony canvas doctor|sync|save`, `plan snapshot|list|open` — `.cursor/skills/canvas-artifacts/SKILL.md`.
