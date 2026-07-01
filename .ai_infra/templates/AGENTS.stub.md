# AGENTS.md

## Just installed?

1. Edit `.local/user_settings/github.collaboration.yaml` → your name + `@handle`
2. `python3 -m cursor_workflow contributors validate`
3. Read `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`
4. **`/implementer`** (or pick `/test-runner`, `/verifier`, `/enterprise-auditor` from the **`/`** menu)

Full walkthrough: [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md)

---

## Project intent

**MAS Workflow Kit** — multi-agent workflow installed via plugin. Agents call **one script command** per maintainer action; `GATES` live in `.ai_infra/scripts/pr/prepare.py`.

## First reads

1. [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md)
2. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — artifact tiers
3. [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md)
4. `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`

## Rules (always applied in Cursor)

| Rule | Topic |
|------|--------|
| `.cursor/rules/implementation-workflow-governance.mdc` | Slice lifecycle, trackers, tests |
| `.cursor/rules/pr-workflow-enforcement.mdc` | PR-first, artifacts, branch safety |
| `.cursor/rules/commit-trailer-format.mdc` | Commit trailers + optional `Assisted-by` |
| `.cursor/rules/file-docstring-header-relations.mdc` | **File headers** on new sources |
| `.cursor/rules/local-artifact-protection.mdc` | Protected paths (`.coverage`, `.env`) |
| `.cursor/rules/advisory-audit-alignment-enforcement.mdc` | Architecture audits → alignment artifacts |

Product overlays: `overlays/rules/` at install time.

## Quality gates

`GATES` in `.ai_infra/scripts/pr/prepare.py` — say *prepare gates green* in chat; do not paste full gate lists.
