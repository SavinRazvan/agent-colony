# Install scripts

Scaffold the universal **Agent Colony** into a consumer project.

## Usage

From the **agent-colony** product repo root:

```bash
# Preview
python .ai_infra/scripts/install/scaffold.py --target /path/to/new-project --dry-run

# Consumer install (layout verified in-process; no tests/ smoke file by default)
python .ai_infra/scripts/install/scaffold.py \
  --target /path/to/new-project \
  --with-venv \
  --with-mcp-json \
  --verify

# Kit dev: copy full tests/ tree
python .ai_infra/scripts/install/scaffold.py \
  --target /path/to/new-project \
  --with-tests \
  --with-venv \
  --verify
```

Copies `project.config.yaml.example` to the target (rename to `project.config.yaml` after install). See [`docs/operations/project-config.md`](../../docs/operations/project-config.md).

## Options

| Flag | Effect |
|------|--------|
| `--target` | Destination directory (required) |
| `--source` | Kit root (default: auto-detect) |
| `--dry-run` | Print copy plan only |
| `--with-readme` | Copy kit `README.md` |
| `--with-tests` | Copy full kit `tests/` (kit dev only) |
| `--keep-smoke-test` | Opt-in: write `tests/modules/smoke/test_kit_installed.py` (default: omit; layout checked in-process) |
| `--with-venv` | Create `.venv`, install pytest + mcp |
| `--with-mcp-json` | Merge `mcp.json.kit.example` (+ `mcp.user.json` if present) → `mcp.json` |
| `--verify` | Run `check_testing_artifacts`, `pytest -q`, governance + debrand |

After install, apply product rules manually:

```bash
cp overlays/rules/*.mdc /path/to/target/.cursor/rules/
```

## Makefile

```bash
make install-dry-run
```

Installs to `/tmp/agent-colony-dry-run` and runs verification gates.

See [`docs/operations/install-dry-run.md`](../../docs/operations/install-dry-run.md).
