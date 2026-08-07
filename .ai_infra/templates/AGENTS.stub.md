# AGENTS.md

## Installing?

1. Agent chat:

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

[screenshot](.ai_infra/docs/operations/assets/agent-colony-install.png) · [step-by-step](.ai_infra/docs/operations/consumer-quickstart.md#step-1-detail--install-plugin-from-github)

2. Open **your app folder** → Agent chat:

```text
/workflow-activate
```

**First install note:** if activate fails with *No module named agent_colony*, use the Cursor plugin cache payload (after `/add-plugin`):

```bash
PAYLOAD="$(ls -1dt ~/.cursor/plugins/cache/agent-colony/agent-colony/*/payload 2>/dev/null | head -1)"
python3 "$PAYLOAD/agent_colony" activate --directory . --source "$PAYLOAD"
```

Details: [consumer-quickstart § First activate troubleshooting](.ai_infra/docs/operations/consumer-quickstart.md#first-activate-troubleshooting).

## Just installed?

1. Edit `.local/user_settings/github.collaboration.yaml` → your name + `@handle`
2. `source .venv/bin/activate && python3 -m agent_colony contributors validate` (**must PASS**)
3. If `project_ssot.enabled: true`:
   - `gh auth status` — if Project scopes missing: `gh auth refresh -h github.com -s read:project,project` ([PLUGIN-USER-GUIDE § GitHub CLI auth](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#github-cli-auth-projects))
   - Agent chat **`/board`** + paste **Project URL** + **repo URL** → agent wires `project_ssot` ids + `default_repo` (confirm before save)
   - `source .venv/bin/activate && python3 -m agent_colony project doctor` (expect **ok**)
   - **Minimal 2-view shell** (recommended — matches [Playground #3](https://github.com/users/SavinRazvan/projects/3)):
     ```bash
     cp .ai_infra/templates/user-settings/exemplars/board-shell.schema.minimal.yaml \
        .local/user_settings/board-shell.schema.yaml
     ```
     GitHub UI: **Prioritized backlog** (Table) + **Status board** (Board, group by Status) with Tier-1 columns on both.
   - **`/board`** → **CONSENT GATE** + **TURN PROTOCOL** (one view per turn; [views-setup.md](.ai_infra/templates/project-board/views-setup.md))
   - Re-run `board-bootstrap --check` until **exit 0**
   - `source .venv/bin/activate && python3 -m agent_colony project status`
   - Day-to-day board protocol: `board-ssot` skill (loaded automatically); wire + shell coach: **`/board`**
4. If Project SSOT is disabled: read `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`
5. **`/implementer`** when bootstrap is green (not day-0: `/auditor`)

**Dashboards (optional):** from project root:

```bash
python3 -m http.server 8000
```

Open http://localhost:8000/.local/agents-control-center/dashboards/index.html *(not `file://`)*.

Full walkthrough: [PLUGIN-USER-GUIDE.md](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) · [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md)

---

## Project intent

**Agent Colony** — multi-agent workflow installed via plugin. Agents call **one script command** per maintainer action; merge gate order lives in `.ai_infra/scripts/pr/prepare.py` **`resolve_gates()`** (`GATES` = 2-gate back-compat alias).

## First reads

1. [`.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md`](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md)
2. [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md)
3. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — artifact tiers
4. [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md)
5. When `project_ssot.enabled` + `board_only`: `python3 -m agent_colony project status` (board-first). Else / offline: `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`

## Rules (always applied in Cursor)

**7 rules** — 6 universal kit rules plus `project-ssot-precedence.mdc` when Project SSOT is enabled (ADR-008).

| Rule | Topic |
|------|--------|
| `.cursor/rules/implementation-workflow-governance.mdc` | Slice lifecycle, trackers, tests |
| `.cursor/rules/pr-workflow-enforcement.mdc` | PR-first, artifacts, branch safety |
| `.cursor/rules/commit-trailer-format.mdc` | Commit trailers + optional `Assisted-by` |
| `.cursor/rules/file-docstring-header-relations.mdc` | **File headers** on new sources |
| `.cursor/rules/local-artifact-protection.mdc` | Protected paths (`.coverage`, `.env`) |
| `.cursor/rules/advisory-audit-alignment-enforcement.mdc` | Architecture audits → alignment artifacts |
| `.cursor/rules/project-ssot-precedence.mdc` | Board SSOT precedence when `project_ssot.enabled` (ADR-008) |

## Commits

Required trailers: `.cursor/rules/commit-trailer-format.mdc` — set identity in `github.collaboration.yaml`, then `python3 -m agent_colony contributors validate`.

## Quality gates

**Default merge gate order** is `resolve_gates()` in `.ai_infra/scripts/pr/prepare.py` — say *prepare gates green* in chat; do not paste full gate lists.
