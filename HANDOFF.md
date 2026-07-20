<!--
File: HANDOFF.md
Path: HANDOFF.md
Role: Kit-dev product front door — STANDALONE identity, board SSOT north star, pointers to durable docs.
Used By:
 - Cursor agents opening this workspace
 - Maintainer onboarding
Depends On:
 - .local/user_settings/github.collaboration.yaml (identity + project_ssot)
 - .ai_infra/docs/decisions/ADR-008-project-board-ssot.md
 - .ai_infra/docs/operations/project-board-collaboration.md
 - .ai_infra/docs/operations/PLUGIN-USER-GUIDE.md
Notes:
 - Not shipped to consumers via activate; consumers use PLUGIN-USER-GUIDE + collab YAML.
 - Lineage tip at mirror: mas-workflow-kit 8a779fa / v0.4.0 (merge 1cb6dd7). STANDALONE 2026-07-18.
-->

# HANDOFF — MAS Workflow Kit · Project SSOT

**Audience:** maintainers and agents working in **this** repository (`mas-workflow-kit-project-ssot`).  
**Not for consumers:** plugin install and app-repo activate are documented in [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) (§ Product promise).

Read this file first in Cursor, then [`AGENTS.md`](AGENTS.md) for day-to-day execution.

---

## Identity

| | |
|--|--|
| **Product** | [mas-workflow-kit-project-ssot](https://github.com/SavinRazvan/mas-workflow-kit-project-ssot) |
| **Lineage (read-only)** | [mas-workflow-kit](https://github.com/SavinRazvan/mas-workflow-kit) · tip at mirror `8a779fa` / tag `v0.4.0` |
| **Standing** | **STANDALONE** (2026-07-18) — permanent product; **do not** port doctrine back upstream |
| **Owner** | Savin Ionuț Răzvan · `@SavinRazvan` |
| **Board** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) · `#3` · `PVT_kwHOBl46-84A9KZx` |
| **Settings** | `.local/user_settings/github.collaboration.yaml` (`owner` + `project_ssot`) |

Field and option ids live in that YAML (and the exemplar under `.ai_infra/templates/user-settings/`). Do not duplicate them here.

---

## North star

This repository **is** the product: installable multi-agent workflow infrastructure with a **GitHub Project** as the only writable coordination SSOT when `project_ssot.enabled` and `sync_policy: board_only`.

| Surface | Role |
|---------|------|
| **GitHub Project** | Backlog, Status, Priority/Size, multi-agent continuation. **Entry** = read board; **Exit** = update Status + Notes. |
| **Local `.local/`** | Evidence only (PR Pattern A, audits, gates, secrets, coverage, outbox). Never a second Status writer under `board_only`. |

**Non-negotiables**

- No dual-write of Status to `work-tracker.md` / `session-pointer.md` when `board_only`.
- No merge of this product’s board doctrine into upstream `mas-workflow-kit`.
- Create shippable cards as **Issues** (`item_kind_default: issue`). Draft is scratch-only.
- Fill **Tier-1** fields (Status, Priority, Size/Estimate per skill rubric, Start date on first In progress, Assignee, Linked PR via `mention-pr`).
- GraphQL throttle / Forbidden / precheck low quota → EXIT_QUEUED (6) / `project outbox` (do not retry-loop); flush after reset — outbox is not SSOT.

Doctrine detail: [ADR-008](.ai_infra/docs/decisions/ADR-008-project-board-ssot.md) · ops [project-board-collaboration.md](.ai_infra/docs/operations/project-board-collaboration.md) · skill [project-board-ssot](.cursor/skills/project-board-ssot/SKILL.md).

---

## Session start (this repo)

```bash
python3 -m cursor_workflow project status
python3 -m cursor_workflow project list --status ready
# claim / create-from-template — see: python3 -m cursor_workflow project guide
```

Auth (board write): `gh auth refresh -h github.com -s read:project,project` (keep `repo`).  
No browser (WSL)? Copy the one-time code → **https://github.com/login/device** → approve Project permissions → `gh auth status`.  
Full walkthrough: [PLUGIN-USER-GUIDE § GitHub CLI auth](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#github-cli-auth-projects).

If the board is unavailable: `fallback: local_trackers` only, then resume board sync. Never invent a second Status SSOT.

---

## Where detail lives (do not duplicate)

| Topic | Canonical path |
|-------|----------------|
| Consumer install / Product promise | [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) |
| Shipped vs spec | [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) |
| Repo map (kit vs payload) | [repository-map](.ai_infra/docs/handoff/repository-map.md) |
| Agent roster / gates / commits | [AGENTS.md](AGENTS.md) |
| PR merge path | [.agents/skills/pr-workflow](.agents/skills/pr-workflow/SKILL.md) |
| MCP connect | [connect-external-mcp](.ai_infra/docs/operations/connect-external-mcp.md) |

---

## Agent roster (kit-dev)

| Agent | Role |
|-------|------|
| `project-board` | Board triage / recipes (independent-governed) |
| `implementer` | Product slices; board-first Entry/Exit |
| `test-runner` / `verifier` | Tests and claim verification |
| `enterprise-auditor` | Alignment / scorecard → `.local/workflow-artifacts/` |
| `workflow-drift-guard` | DRIFT-009/010; board on Exit |
| `integrator-mas-agent` | Agents, skills, MCP, kit expansions |
| `researcher` | Shipped/proven corpus researcher — adaptive Brief; packs under `_research_results/` (opt-in after `research init`); hard-stop on product code · live E2E Issue #74 |

Do **not** publish marketplace releases from this repo against upstream `mas-workflow-kit`.

---

## Deferred product backlog (board)

Scheduled only when claimed from the Project (Backlog → Ready).

- **Deferred (Backlog):** marketplace publish (**EA-019**) — **prep done** (PR #72 + dry-run `marketplace-dry-run-2026-07-19`); **live public Marketplace postponed** (maintainer 2026-07-19). Consumers use `/add-plugin` until listed. Checklist: [marketplace-publish.md](.ai_infra/docs/handoff/marketplace-publish.md).
- **Closed hygiene (2026-07-19):** EA-020 `gh_project_adapter` thinning (EA-001 + coverage enough); EA-024 ICC module-map tab (ICC deprecated; map at `.local/module-map.md`).
- **Prose-only (no board card):** always-on GitHub Actions bots; MCP-before-`gh` for board writes.

---

## History (one paragraph)

Mirrored from `mas-workflow-kit` on 2026-07-17 (`1cb6dd7`). Board SSOT, Pattern A CLI, Tier-1 fields, Issue-at-create default, and STANDALONE were decided and shipped through 2026-07-19. Prior session evidence (consumer Smart-Notes gates, early board smoke option tables) is superseded by live YAML + ADR-008 — do not treat this file as a changelog.

---

**Last updated:** 2026-07-19 · **Next:** `project status` → claim Ready (or schedule deferred Backlog, e.g. EA-019 live Marketplace when ready)
