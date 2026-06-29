# ADR-005: Consumer vs maintainer docs split

**Status:** accepted  
**Date:** 2026-06-14

## Context

Maintainer-only checklists were copied to consumers via `docs/operations/`. Root megadocs reference removed paths.

## Decision

| Audience | Location | Installed? |
|----------|----------|------------|
| Consumer | `.ai_infra/docs/operations/`, `governance/`, `roadmap/`, `decisions/`, `architecture/` | Yes (manifest) |
| Maintainer | `.ai_infra/docs/maintainer/`, `handoff/` | Kit dev only |

Decontaminate consumer ops/governance of product-specific paths, legacy `src/` references, and product API docs.

## Consequences

- Phase 4 moves megadocs to `.ai_infra/docs/maintainer/`
- `documentation-maintenance-checklist.md` is kit-scoped only
