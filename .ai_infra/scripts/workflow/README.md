# Workflow drift scripts

Operational workflow drift detection per [ADR-007](../../docs/decisions/ADR-007-workflow-drift-guard.md).

## Commands

```bash
python .ai_infra/scripts/workflow/check_drift.py --directory .
python -m agent_colony drift validate --directory .
make drift-validate
```

## Checks

See `drift_checks.py` — DRIFT-001…010 + 004b on kit-dev (004b/009–010 when `project_ssot.sync_policy: board_only`); consumer profile runs DRIFT-005 + DRIFT-008 only.

**DRIFT-005 on consumer:** When `IMPLEMENTATION-STATUS.md` is absent (normal on plugin installs), the check **PASSes (skip)** — not a consumer failure. A FAIL on missing file indicates an older kit payload (false positive; see `consumer-quickstart.md`).

Exit code 1 on P0 failure only.
