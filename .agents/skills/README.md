# `.agents/skills`

Standards-friendly skills location (alongside `.cursor/skills/`, which Cursor loads from git).

## Layout

Each skill: **`<skill-name>/SKILL.md`**.

## This repo

| Area | Where |
|------|--------|
| Implementation loop | `.cursor/skills/implementation-execution-loop/`, `.cursor/agents/implementer.md`, `implementation-workflow-governance.mdc` |
| Tests | `.cursor/skills/test-module-coverage/`, `.cursor/agents/test-runner.md` |
| **Maintainer PR** | **`PR_WORKFLOW.md`** + `review-pr` / `prepare-pr` / `merge-pr`; audits via **`enterprise-auditor`** (see `.cursor/agents/enterprise-auditor.md`); commit trailers: **`.cursor/rules/commit-trailer-format.mdc`** (`Author` / `GitHub-User`, optional `Assisted-by`) |
| **Research corpus** | **`RESEARCH_WORKFLOW.md`** + `.cursor/skills/research-corpus-execution/` + `.cursor/agents/researcher.md`; output gitignored: **`_research_results/`** |
| **Enterprise architecture audit** | `.cursor/skills/enterprise-architecture-audit/SKILL.md` + entry stub `enterprise-architecture-audit/` here (`audit-alignment/` is a deprecated redirect) |
| Scripts | `.ai_infra/scripts/pr/review.py`, `prepare.py`, `merge.py`, `finalize.py`, `verify_publish.py` |

Live trackers (gitignored): **`.local/index-and-planning/current/*.md`**. Full map: **`docs/operations/local-workspace-layout.md`**. Handoff checklist: **`docs/operations/workflow-complete.md`** §F (not a duplicate file under `.local/`).
