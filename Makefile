.PHONY: install-dry-run test gates sync-plugin check-plugin integrate-validate drift-validate

install-dry-run:
	rm -rf /tmp/workflow-kit-dry-run
	.venv/bin/python -m cursor_workflow install \
		--target /tmp/workflow-kit-dry-run \
		--with-venv \
		--with-mcp-json \
		--verify

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
