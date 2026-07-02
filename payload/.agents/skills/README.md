# `.agents/skills`

Maintainer slash-command skills and workflow docs. **Canonical protocols** live under [`.cursor/skills/`](../.cursor/skills/) — Cursor discovers both roots; do not duplicate folder names here.

## Layout

Each skill: **`<skill-name>/SKILL.md`**.

## This repo

| Area | Where |
|------|--------|
| Implementation loop | `.cursor/skills/implementation-execution-loop/`, `.cursor/agents/implementer.md` |
| Tests | `.cursor/skills/test-module-coverage/`, `.cursor/agents/test-runner.md` |
| **Maintainer PR** | **`pr-workflow/`** + `review-pr` / `prepare-pr` / `merge-pr` (`PR_WORKFLOW.md` = legacy redirect) |
| **Research corpus** | `RESEARCH_WORKFLOW.md` + `.cursor/skills/research-corpus-execution/` |
| **Enterprise audit** | `.cursor/skills/enterprise-architecture-audit/SKILL.md` + `.cursor/agents/enterprise-auditor.md` |
| **Drift guard** | `.cursor/skills/workflow-drift-audit/SKILL.md` + `.cursor/agents/workflow-drift-guard.md` |
| **Audit orchestration** | `.cursor/skills/audit-orchestration/SKILL.md` |
| Deprecated redirect | `audit-alignment/` → use `enterprise-auditor` |
| Scripts | `.ai_infra/scripts/pr/review.py`, `prepare.py`, `merge.py`, `finalize.py` |

Plugin sync: `.cursor/skills/` wins; maintainer skills here are **additive only** (see `sync_plugin_bundle.py`).
