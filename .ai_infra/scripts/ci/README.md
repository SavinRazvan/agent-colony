# CI workspace seed

Seeds gitignored `.local/` from versioned fixtures before kit-quality gates.

```bash
python .ai_infra/scripts/ci/seed_kit_workspace.py --directory .
make ci-seed
```

Fixtures: `.ai_infra/templates/local-workspace/ci/kit-dev/`
