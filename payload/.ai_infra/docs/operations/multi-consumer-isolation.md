<!--
File: multi-consumer-isolation.md
Path: .ai_infra/docs/operations/multi-consumer-isolation.md
Role: SSOT for multi-consumer / multi-collaborator file isolation (Model A).
Used By:
 - consumer-quickstart.md
 - PLUGIN-USER-GUIDE.md
 - workflow-architecture.md
Depends On:
 - ADR-001-distribution-activation.md
 - ADR-008-project-board-ssot.md
 - ADR-010-canvas-plan-local-artifacts.md
 - local-workspace-layout.md
 - upgrade-kit.md
Notes:
 - One universal Marketplace payload; isolation is post-activate placement + gitignore.
-->

# Multi-consumer isolation

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

## Product promise

Install the **Agent Colony** plugin once in Cursor. Run **`/workflow-activate`** in **your** app repo. The **same universal payload** copies kit agents, scripts, and CLI. Edit **only** `.local/user_settings/` for identity and **your** GitHub Project. Nothing under `.local/` is shared with other customers or committed to git. Kit files in your repo are **your team's pinned copy** of the product — upgrade when **you** choose via `update` + PR.

## Three boundaries

| Boundary | What | Isolation |
|----------|------|-----------|
| **Marketplace** | `payload/` kit (one version for all) | Read-only product; no customer data |
| **Per repo** | Committed kit + product code | Separate git remote per customer app |
| **Per clone** | `.local/`, secrets, venv | Gitignored; DRIFT-013 enforces |
| **Per team (API)** | GitHub Project | One Project per customer app; Notes `@user/agent` |

**Plugin vs disk:** The Marketplace plugin loads agents/skills/rules in the **IDE only** — it does not write project files. Isolation starts after **`activate`** copies three planes into **that** workspace. See [PLUGIN-ARCHITECTURE.md](../handoff/PLUGIN-ARCHITECTURE.md).

## Class table

| Class | Paths | Git? | Who writes | Update / activate |
|-------|-------|------|------------|-------------------|
| **Kit-managed** | `.cursor/agents` (8 ids), `.cursor/skills/`, `.cursor/rules/`, `.agents/skills/`, `.ai_infra/`, `agent_colony/` | Yes (team) | Kit via activate/update | Full upgrade overwrites; see preserve table |
| **Product** | `src/`, app `tests/`, `docs/`, `overlays/rules/` | Yes (team) | Humans + PRs | Never touched by kit activate |
| **Private runtime** | `.local/**`, `.venv/`, `.env`, `.cursor/mcp.user.json`, MCP secrets | **No** | Each developer | Copy-if-missing; never overwrite `user_settings/` |
| **API SSOT** | GitHub Project Status, Notes | N/A | `project` CLI | Not files; per customer Project |

## Preserve vs overwrite

| Path / area | Re-activate (planes ready) | Full `update` / `--force` |
|-------------|---------------------------|---------------------------|
| `.local/user_settings/` | **Preserved** | **Preserved** |
| Trackers under `.local/index-and-planning/` | **Preserved** (copy-if-missing) | **Preserved** |
| `AGENTS.md` | **Preserved** if present | **Preserved** if present |
| `.cursor/mcp.user.json` | **Preserved** | **Preserved** |
| Dashboard HTML, `pages.json` under `.local/agents-control-center/` | **Refreshed** | **Refreshed** |
| `.cursor/agents`, skills, rules | Skipped (no full install) | **Overwritten** from payload |
| `.ai_infra/`, `agent_colony/` | Skipped | **Overwritten** |
| `.ai_infra/.kit-version` | Healed if stale | **Updated** from source manifest |

Canon: [upgrade-kit.md](upgrade-kit.md) § What install updates.

Run `python3 -m agent_colony update --check` before `--force` to see local deltas on kit-managed paths (agents, skills, rules, `.ai_infra/`, `agent_colony/` per [install-contract.json](../../install-contract.json)).

## Overlay rule collisions

Overlay rules copy into `.cursor/rules/` at activate. If an overlay basename matches a kit rule file, activate may **overwrite** the kit copy on the next refresh.

| Do | Do not |
|----|--------|
| Name overlays `product-*.mdc` | Reuse kit rule basenames (`implementation-workflow-governance.mdc`, etc.) |
| Keep product policy in `overlays/rules/` | Edit kit `.cursor/rules/` in place for product-only policy |

Activate prints a **WARN** when a collision is detected. Prefer integrator-owned **agents** for new automation ids; see [ADR-006](../decisions/ADR-006-agent-integration-model.md).

## Canvas tiers (ADR-010)

| Tier | Location | Git? | Role |
|------|----------|------|------|
| Product | Repo `canvases/*.canvas.tsx` | Yes | Durable product docs / diagrams |
| Session | `.local/canvases/` | No | Ephemeral agent evidence |
| Render bridge | Cursor managed path | N/A | IDE display only |

Promote session → product via human PR; do not store product truth only in `.local/`.

## Scenario A — Separate customer repos

Each company activates into **its own** remote. No cross-repo `.local/` coupling. Each wires **its own** GitHub Project in gitignored `github.collaboration.yaml`.

**Reference:** `module-ai` — ~307 kit paths on GitHub `main`, **0** paths under `.local/` tracked; board Project #4 wired only locally.

## Scenario B — Teammates, same repo

| Concern | Mechanism |
|---------|-----------|
| Shared kit version | Committed `.cursor/`, `.ai_infra/`, `.kit-version` — upgrade via one PR |
| Personal identity / secrets | Each clone: own `.local/user_settings/`, `mcp.user.json` |
| Coordination | GitHub Project when `board_only`; one In progress card per assignee |
| PR artifacts | `.local/workflow-artifacts/` — gitignored |

Kit merge conflicts on `.cursor/` are **intentional shared infrastructure** — not settings overlap. Use integrator **new** agent ids; do not fork the eight kit agents in place.

## Hard rules

1. Never commit `.local/`, `.venv/`, `.env`, `mcp.user.json`, or MCP secrets — enforce with `drift validate --profile consumer` (DRIFT-013).
2. Wire board + identity only in `.local/user_settings/github.collaboration.yaml`.
3. Do not embed customer Project ids in committed kit files.
4. Do not edit the eight kit agent files in place — use `/integrator` for new agent ids.
5. Kit upgrade = one PR per repo; run `update --check` before `--force`.
6. Overlay rules use `product-*.mdc`; never reuse kit rule basenames.

## Recovery (tracked runtime)

If DRIFT-013 fails because `.local/` or `.venv/` was committed:

1. Keep healed `.gitignore` (re-run `activate` or `update` heal).
2. `git rm -r --cached .local .venv` (and `.env` if needed).
3. Commit the index fix.

See [upgrade-kit.md](upgrade-kit.md) § Consumer heal.

## Rejected: gitignore kit paths by default

Gitignoring `.cursor/` and `.ai_infra/` after activate would avoid git merge fights but causes **silent kit version drift**, **CI must activate every job**, and **integrator agents not shared via git**. Model A (committed kit + gitignored `.local/`) is the supported contract.

## Maintainer checklist (payload)

- [ ] Single `payload/` from `make sync-plugin`
- [ ] `kit_version` in manifest + `.kit-version` stamp on activate
- [ ] Exemplars only under `templates/user-settings/` — no live customer YAML
- [ ] `make install-dry-run` + `check_consumer_purity.py` PASS before release
- [ ] No customer Project ids in generated trees

## Customer checklist

- [ ] `.gitignore` includes `.local/` (activate appends if missing)
- [ ] `contributors validate` after editing `user_settings/`
- [ ] `project doctor` + board-bootstrap for **your** Project
- [ ] `drift validate --profile consumer` in CI (optional template: `.ai_infra/templates/ci/consumer-gates.yml`)
- [ ] `git ls-files .local/` prints nothing

## Kit-managed paths (contract)

Listed in [install-contract.json](../../install-contract.json) `kit_managed_globs` — `update --check` diffs every matching file on disk against the payload source before a full refresh.

## Related

- [local-workspace-layout.md](local-workspace-layout.md)
- [folder-charter.md](../governance/folder-charter.md)
- [ADR-006](../decisions/ADR-006-agent-integration-model.md) (integrator extensions; extra agents are team-owned if committed)
- [ADR-007](../decisions/ADR-007-workflow-drift-guard.md) (DRIFT-013, DRIFT-011b)
- [consumer-quickstart.md](consumer-quickstart.md)
