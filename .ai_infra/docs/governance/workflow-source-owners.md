<!--
File: workflow-source-owners.md
Path: .ai_infra/docs/governance/workflow-source-owners.md
Role: Canonical ownership map for workflow surfaces (scripts vs docs vs agents).
Used By:
 - .ai_infra/docs/governance/README.md
 - Maintainers resolving conflicts between README, rules, and skills
Depends On:
 - .ai_infra/docs/operations/workflow-complete.md
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/scripts/pr/local_workflow_paths.py
Notes:
 - Executable behavior wins over prose; prose must link to scripts instead of copying steps.
 - Last reviewed: 2026-06-14
-->

# Workflow source owners

| Concern | Canonical owner | Consumers |
|---------|-----------------|-----------|
| Prepare gate **order** and commands | `.ai_infra/scripts/pr/prepare.py` (`GATES`) | Rules, skills, `workflow-complete.md`, `AGENTS.md` |
| PR artifact **paths** | `.ai_infra/scripts/pr/local_workflow_paths.py` | `review.py`, `prepare.py`, `merge.py`, rules |
| PR publish verification | `.ai_infra/scripts/pr/verify_publish.py` | Pre-PR branch health |
| Merge preconditions | `.ai_infra/scripts/pr/merge.py` | `merge-pr` skill |
| Post-merge cleanup | `.ai_infra/scripts/pr/finalize.py` | `merge-pr` skill |
| Maintainer narrative order | `.agents/skills/PR_WORKFLOW.md` | Humans |
| Durable maintainer checklist | `.ai_infra/docs/operations/workflow-complete.md` | Everyone (versioned) |
| Audit / dedup rules | `.ai_infra/docs/operations/agent-workflow-procedures.md` | Alignment + governance |
| Maintainer doc sync checklist | `.ai_infra/docs/operations/documentation-maintenance-checklist.md` | Slice/PR doc updates |
| Alignment finding shape | `.ai_infra/docs/roadmap/alignment-audit-schema.md` | `enterprise-auditor` focused pass |
| Full enterprise audit outputs | `.cursor/skills/enterprise-architecture-audit/SKILL.md` → `.local/workflow-artifacts/enterprise-architecture-audit/` | Deep audits |
| Focused alignment outputs | Same skill § focused pass → `.local/workflow-artifacts/alignment/` | Architecture-impacting PRs |
| Always-on enforcement | `.cursor/rules/*.mdc` | Cursor agents |
| Git **commit** trailers | `.cursor/rules/commit-trailer-format.mdc` | `AGENTS.md` § Commits, implementer skills |
| Governance drift scan | `.ai_infra/scripts/architecture/check_governance_consistency.py` | CI + local policy edits |
| Path resolution | `.ai_infra/paths.py` | MCP, install scaffold, tests |
| MCP registry mapping | `.cursor/mcp.registry.yaml` | Agents, `connect-external-mcp.md` |
| External MCP connect procedure | `.ai_infra/docs/operations/connect-external-mcp.md` | Users + agents |
| Repository orientation | `AGENTS.md`, `README.md` | All agents |

**Rule:** If text disagrees with `prepare.py` or `local_workflow_paths.py`, update the text in the **same PR** as the script change, or immediately after.

**PR artifacts vs git commits:** `.local/workflow-artifacts/pr/*.md` use `Action-By` / `Prepared-By` headers. Git commits use `Author:` / `GitHub-User:` (+ optional `Assisted-by:`) per commit-trailer rule — never conflate the two.
