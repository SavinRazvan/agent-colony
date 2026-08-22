# ADR-011: Consumer lite install profile

**Status:** accepted  
**Date:** 2026-08-22

## Context

Fixed Cursor overhead per turn includes always-applied rules (~10 KB at full tier), `AGENTS.md` (~6.5 KB), skill catalog, and MCP tool schemas. Full kit ships 15 skills, 7 rules (4 always-on + 3 requestable after kit 0.7.0), and 8 agents — more than day-to-day consumer implement/verify loops need.

Related: [token-efficiency-program.md](../operations/token-efficiency-program.md), [ADR-001](ADR-001-distribution-activation.md), [ADR-008](ADR-008-project-board-ssot.md).

## Decision

1. Add optional **`consumer_lite`** manifest profile with `skill_allowlist`, `agent_allowlist`, and `agents_md: stub_lite`.
2. Scaffold **prunes** skill dirs and agent `.md` files not in allowlists after copy; rules are **not** deleted — global 4+3 tiering applies to all profiles.
3. Write profile marker to `.local/generated-data/install-profile.json` on activate.
4. **Lite first-run:** embed CONSENT GATE + TURN PROTOCOL in `board.md` § First-run lite — do **not** ship `board-shell` skill on lite (avoids broken `doc skill-section` references).
5. **Phase 2 (0.7.1):** **`agents_skill_allowlist`** on `consumer_lite` — keeps PR slash skills (`review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `full-pr-workflow`); prunes `audit-alignment` and legacy root MD files. Plain `update` still defaults to `with_mcp` (lite → full on version bump); documented in consumer-lite-profile.
6. Bump **kit_version to 0.7.0** with the initial lite feature set; **0.7.1** adds agents_skill allowlist.

## Consequences

- [consumer-lite-profile.md](../operations/consumer-lite-profile.md) — consumer spec
- [AGENTS.stub-lite.md](../../templates/AGENTS.stub-lite.md) — lite AGENTS template
- DRIFT-014/016 profile-aware validation
- `update --force --profile with_mcp` restores full payload

## Alternatives rejected

| Alternative | Why rejected |
|-------------|--------------|
| Split skill folders per profile in SSOT | Too much sync churn |
| Provider LLM prompt caching | Out of kit scope (Cursor platform) |
| Delete requestable rules on lite | Breaks upgrade path and commit/audit compliance |

## References

- [manifest.yaml](../../manifest.yaml)
- [scaffold.py](../../scripts/install/scaffold.py)
- [board.md](../../../.cursor/agents/board.md)
