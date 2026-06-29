<!--
File: documentation-maintenance-checklist.md
Path: .ai_infra/docs/operations/documentation-maintenance-checklist.md
Role: Recurring checklist to prevent documentation drift in the MAS Workflow Kit.
Used By:
 - .agents/skills/PR_WORKFLOW.md
 - Maintainers during PR preparation
Depends On:
 - .ai_infra/docs/governance/workflow-source-owners.md
Notes:
 - Apply on architecture-impacting or governance changes at minimum.
-->

# Documentation Maintenance Checklist

## Trigger

Run when a PR changes kit architecture, install manifest, governance, workflow policy, or consumer ops docs.

## PR Checklist (required)

- [ ] Confirm impacted canonical docs are updated (`README`, `AGENTS.md`, `.ai_infra/docs/`).
- [ ] If workflow gates or `.cursor/rules` change: sync `workflow-source-owners.md`, `drift-prevention.md`, `rules-overlap-matrix.md`.
- [ ] If alignment audit categories change: sync `.ai_infra/docs/roadmap/alignment-audit-schema.md` and enterprise-audit skill references.
- [ ] If install manifest or scaffold changes: run `make install-dry-run` and update `consumer-quickstart.md`.
- [ ] If ADRs change: update `.ai_infra/docs/decisions/README.md` index.
- [ ] Verify no contradictions against `.cursor/rules/*.mdc` and `.agents/skills/PR_WORKFLOW.md`.
- [ ] Run `python .ai_infra/scripts/architecture/check_governance_consistency.py`.

## Ownership and Cadence

| Area | Owner | Cadence |
|------|-------|---------|
| Kit governance docs | Maintainer | Per REFACTOR slice |
| Consumer ops runbooks | Maintainer | Before kit release |
| Agent surfaces | Maintainer | With path-drift scanner green |
