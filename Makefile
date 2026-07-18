.PHONY: install-dry-run smoke-consumer live-board-smoke test gates sync-plugin check-plugin integrate-validate drift-validate ci-seed verify-all doc-validate type-check coverage-index

install-dry-run:
	rm -rf /tmp/workflow-kit-dry-run
	.venv/bin/python -m cursor_workflow install \
		--target /tmp/workflow-kit-dry-run \
		--with-venv \
		--with-mcp-json \
		--verify
	.venv/bin/python .ai_infra/scripts/architecture/check_consumer_purity.py --target /tmp/workflow-kit-dry-run

smoke-consumer:
	bash .ai_infra/scripts/install/smoke_marketplace.sh

live-board-smoke:
	@command -v gh >/dev/null || (echo "FAIL: gh CLI required"; exit 1)
	@gh auth status >/dev/null 2>&1 || (echo "FAIL: gh auth required — run: gh auth login -h github.com"; exit 1)
	@gh project item-list --help >/dev/null 2>&1 || true
	@if ! gh api graphql -f query='query { viewer { login } }' >/dev/null 2>&1; then \
		echo "FAIL: GitHub API unavailable — check gh auth"; exit 1; \
	fi
	@if gh project item-list 1 --owner @me --limit 1 2>&1 | grep -qi "missing required scopes"; then \
		echo "FAIL: missing Project scopes — run: gh auth refresh -h github.com -s read:project,project"; \
		exit 1; \
	fi
	PROJECT_SSOT_LIVE=1 .venv/bin/python -m pytest -q tests/modules/install/test_project_cli_live.py

test:
	.venv/bin/python -m pytest -q

type-check:
	.venv/bin/pyright

gates:
	.venv/bin/python -m cursor_workflow gates

sync-plugin:
	.venv/bin/python .ai_infra/scripts/release/sync_plugin_bundle.py

check-plugin:
	.venv/bin/python .ai_infra/scripts/release/sync_plugin_bundle.py --check

integrate-validate:
	.venv/bin/python -m cursor_workflow integrate validate --directory .

drift-validate:
	.venv/bin/python -m cursor_workflow drift validate --directory .

doc-validate:
	.venv/bin/python -m cursor_workflow doc validate --directory .

verify-all:
	.venv/bin/python -m cursor_workflow verify all --directory .

ci-seed:
	.venv/bin/python .ai_infra/scripts/ci/seed_kit_workspace.py --directory .

coverage-index:
	.venv/bin/python .ai_infra/scripts/ci/generate_coverage_index.py --directory .
