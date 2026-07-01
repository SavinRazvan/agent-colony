.PHONY: install-dry-run smoke-consumer test gates sync-plugin check-plugin integrate-validate drift-validate ci-seed verify-all doc-validate

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

test:
	.venv/bin/python -m pytest -q

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
