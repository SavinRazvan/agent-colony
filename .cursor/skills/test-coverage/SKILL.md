---
name: test-coverage
description: Module-focused tests and coverage evidence for workflow scripts and project code.
---

# Test coverage

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

`src/**` or `scripts/**` behavior change; coverage or regression requests; medium/high risk before merge.

## Procedure

1. Target modules/symbols; matrix: valid / boundary / invalid, lifecycle, failure/recovery.
2. Tests under `tests/modules/<module>/`.
3. Update `test-index.md` and `test-plan.md`; drop obsolete tests when contracts change.
4. Run scoped `pytest` → broader as needed. Before merge: **`check_testing_artifacts.py`** (via `prepare.py` `resolve_gates()`).
5. Coverage evidence: `pip install -e ".[dev]"` then `pytest --cov=.ai_infra --cov=agent_colony --cov-report=term-missing --cov-report=json -q` (writes **`coverage.json`** only). Record gaps in board Notes when `board_only`, else `work-tracker.md`; one line in `updates-log.md`. Scope: kit import surface; subprocess scanners excluded by design — see `IMPLEMENTATION-STATUS.md` § Coverage scope.
6. **After 100% scoped coverage:** sync `IMPLEMENTATION-STATUS.md`, regenerate `coverage-index.md` via `make coverage-index`, `make doc-validate`, sync README/AGENTS claims, `make sync-plugin` when payload copies change.
7. Report: modules · edges added · gaps · tracker edits.

## Themes (when relevant)

Validation boundaries · error/reason codes · retry/replay · async cleanup · policy negative paths.

## Output

`Coverage summary` → `Tests added/updated` → `Edge cases` → `Gaps` → `Index/plan updates`.
