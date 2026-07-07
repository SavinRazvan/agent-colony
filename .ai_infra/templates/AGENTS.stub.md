# AGENTS.md

## Installing?

1. Agent chat:

```text
/add-plugin https://github.com/SavinRazvan/mas-workflow-kit
```

[screenshot](.ai_infra/docs/operations/assets/mas-workflow-kit-install.png) · [step-by-step](.ai_infra/docs/operations/consumer-quickstart.md#step-1-detail--install-plugin-from-github)

2. Open **your app folder** → Agent chat:

```text
/workflow-activate
```

## Just installed?

1. Edit `.local/user_settings/github.collaboration.yaml` → your name + `@handle`
2. `source .venv/bin/activate && python3 -m cursor_workflow contributors validate`
3. Read `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`
4. **`/implementer`** (or pick `/test-runner`, `/verifier`, `/enterprise-auditor` from the **`/`** menu)

**Dashboards (optional):** from project root:

```bash
python3 -m http.server 8000
```

Open http://localhost:8000/.local/agents-control-center/dashboards/index.html *(not `file://`)*.

Full walkthrough: [PLUGIN-USER-GUIDE.md](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) · [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md)

---

## Project intent

**MAS Workflow Kit** — multi-agent workflow installed via plugin. Agents call **one script command** per maintainer action; `GATES` live in `.ai_infra/scripts/pr/prepare.py`.

## First reads

1. [`.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md`](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md)
2. [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md)
3. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — artifact tiers
4. [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md)
5. `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`

## Rules (always applied in Cursor)

| Rule | Topic |
|------|--------|
| `.cursor/rules/implementation-workflow-governance.mdc` | Slice lifecycle, trackers, tests |
| `.cursor/rules/pr-workflow-enforcement.mdc` | PR-first, artifacts, branch safety |
| `.cursor/rules/commit-trailer-format.mdc` | Commit trailers + optional `Assisted-by` |
| `.cursor/rules/file-docstring-header-relations.mdc` | **File headers** on new sources |
| `.cursor/rules/local-artifact-protection.mdc` | Protected paths (`.coverage`, `.env`) |
| `.cursor/rules/advisory-audit-alignment-enforcement.mdc` | Architecture audits → alignment artifacts |

## Commits

Required trailers: `.cursor/rules/commit-trailer-format.mdc` — set identity in `github.collaboration.yaml`, then `python3 -m cursor_workflow contributors validate`.

## Quality gates

`GATES` in `.ai_infra/scripts/pr/prepare.py` — say *prepare gates green* in chat; do not paste full gate lists.
