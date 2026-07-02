<!--
File: documentation-maintenance-checklist.md
Path: .ai_infra/docs/operations/documentation-maintenance-checklist.md
Role: Recurring checklist to prevent documentation drift in the MAS Workflow Kit.
Used By:
 - .agents/skills/pr-workflow/SKILL.md
 - Maintainers during PR preparation
Depends On:
 - .ai_infra/docs/governance/workflow-source-owners.md
Notes:
 - Apply on architecture-impacting or governance changes at minimum.
-->

# Documentation Maintenance Checklist

> **Kit maintainers only.** Consumer projects receive this file via manifest copy; treat it as maintainer reference unless you fork the kit.

## Trigger

Run when a PR changes kit architecture, install manifest, governance, workflow policy, or consumer ops docs.

## PR Checklist (required)

- [ ] Confirm impacted canonical docs are updated (`README`, `AGENTS.md`, `.ai_infra/docs/`).
- [ ] If workflow gates or `.cursor/rules` change: sync `workflow-source-owners.md`, `drift-prevention.md`, `rules-overlap-matrix.md`, `gate-matrix.md`.
- [ ] If drift guard or integrate validate changes: sync ADR-007, `drift-prevention.md`, `AGENTS.md`, and agent cards.
- [ ] If CI or `.local` seeding changes: sync `gate-matrix.md`, `seed_kit_workspace.py` README, `kit-quality.yml`.
- [ ] After `.ai_infra/docs/` or exemplar changes: run `make sync-plugin` and `make check-plugin`.
- [ ] After agent roster, rules count, or IMPLEMENTATION-STATUS changes: run `make doc-validate`.
- [ ] If alignment audit categories change: sync `.ai_infra/docs/roadmap/alignment-audit-schema.md` and enterprise-audit skill references.
- [ ] If install manifest, scaffold, or activate flow changes: run `make install-dry-run`, update `PLUGIN-USER-GUIDE.md`, `consumer-quickstart.md`, `PLUGIN-ARCHITECTURE.md`, and `workflow-activate` skill.
- [ ] If ADRs change: update `.ai_infra/docs/decisions/README.md` index.
- [ ] Verify no contradictions against `.cursor/rules/*.mdc` and `.agents/skills/pr-workflow/SKILL.md`.
- [ ] Run `python .ai_infra/scripts/architecture/check_governance_consistency.py`.

## Ownership and Cadence

| Area | Owner | Cadence |
|------|-------|---------|
| Kit governance docs | Maintainer | Per REFACTOR slice |
| Consumer ops runbooks | Maintainer | Before kit release |
| Agent surfaces | Maintainer | With path-drift scanner green |
| Drift / integrate / CI seed docs | Maintainer | When ADR-007 slices or `kit-quality.yml` change |
