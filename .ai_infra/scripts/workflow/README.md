# Workflow drift scripts

Operational workflow drift detection per [ADR-007](../../docs/decisions/ADR-007-workflow-drift-guard.md).

## Commands

```bash
python .ai_infra/scripts/workflow/check_drift.py --directory .
python -m cursor_workflow drift validate --directory .
make drift-validate
```

## Checks

See `drift_checks.py` — DRIFT-001…008. Profile `kit-dev` (default) or `consumer` (when `STARTER-001` in work-tracker).

Exit code 1 on P0 failure only.
