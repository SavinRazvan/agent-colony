# ADR-001: Distribution activation

**Status:** accepted  
**Date:** 2026-06-14

## Context

The kit ships via CLI (`cursor_workflow install`) and will ship as a Cursor Marketplace plugin. Agents reference `.ai_infra/scripts/` which must exist in consumer projects.

## Decision

**Option B (locked):** Marketplace plugin ships `payload/.ai_infra/` plus a `workflow-activate` skill that runs `cursor_workflow activate` (install/verify into `${workspace}`). Plugin is self-contained without requiring a separate kit clone.

## Consequences

- Phase 6 implements `sync_plugin_bundle.py` and payload layout.
- CLI install remains supported for kit developers and advanced users.
- ADR reviewed before Marketplace publish.
