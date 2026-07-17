# Testing Plan

## Objective

- Keep tests modular, high-signal, and aligned with source boundaries.
- CI seeds this file from `.ai_infra/templates/local-workspace/ci/kit-dev/`.

## Coverage policy

- Default gate: `pytest -q` (via `prepare.py` `GATES`)
- Kit CI: `kit-quality.yml` runs seed + full gate matrix (no `--cov-fail-under`)

## Active priorities

- [x] CI workspace seed before gates
- [ ] Keep `test-index.md` synced when modules change
