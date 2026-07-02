#!/usr/bin/env bash
# File: smoke_marketplace.sh
# Path: .ai_infra/scripts/install/smoke_marketplace.sh
# Role: Manual marketplace / consumer install smoke (Track A kit + Track B payload).
# Used By:
#  - Makefile smoke-consumer
#  - .ai_infra/docs/handoff/marketplace-publish.md
# Depends On:
#  - cursor_workflow install / activate
#  - check_consumer_purity.py
# Notes:
#  - Run from kit repo root. Requires .venv/bin/python.

set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PY="${KIT}/.venv/bin/python"
SMOKE="${SMOKE:-/tmp/mas-smoke-$(date +%Y%m%d-%H%M)}"
PLUGIN_TARGET="${PLUGIN_TARGET:-/tmp/mas-smoke-plugin-$(date +%Y%m%d-%H%M)}"

if [[ ! -x "$PY" ]]; then
  echo "FAIL: missing kit venv at $PY — run: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt"
  exit 1
fi

echo "=== MAS Workflow Kit consumer smoke ==="
echo "KIT=$KIT"
echo "SMOKE=$SMOKE"
echo "PLUGIN_TARGET=$PLUGIN_TARGET"
echo

cd "$KIT"
"$PY" .ai_infra/scripts/release/sync_plugin_bundle.py
"$PY" .ai_infra/scripts/release/sync_plugin_bundle.py --check

rm -rf "$SMOKE"
"$PY" -m cursor_workflow install \
  --target "$SMOKE" \
  --with-venv \
  --with-mcp-json \
  --verify

echo
echo "=== TRACK A: direct install checks ==="
"$PY" .ai_infra/scripts/architecture/check_consumer_purity.py --target "$SMOKE"
test ! -d "$SMOKE/.ai_infra/templates/local-workspace/ci"

"$PY" - "$SMOKE" <<'PY'
import json
import sys
from pathlib import Path

smoke = Path(sys.argv[1])
config = smoke / ".local/agents-control-center/config"
pages = json.loads((config / "pages.json").read_text(encoding="utf-8"))
for page in pages["pages"]:
    rel = page["file"]
    if rel.startswith("../../workflow-artifacts/"):
        print(f"SKIP {page['id']} (Tier 2)")
        continue
    ok = (config / rel).resolve().is_file()
    if not ok:
        raise SystemExit(f"FAIL {page['id']}: {rel}")
    print(f"PASS {page['id']}: {rel}")
PY

"$SMOKE/.venv/bin/python" -m cursor_workflow gates --directory "$SMOKE"
"$SMOKE/.venv/bin/python" -m pytest -q "$SMOKE/tests/modules/smoke/"

echo
echo "=== TRACK A: user_settings idempotency ==="
sed -i 's/Your Full Name/SMOKE_CUSTOM_USER/' "$SMOKE/.local/user_settings/github.collaboration.yaml"
"$PY" -m cursor_workflow install \
  --target "$SMOKE" \
  --with-venv \
  --with-mcp-json \
  --verify
grep -q "SMOKE_CUSTOM_USER" "$SMOKE/.local/user_settings/github.collaboration.yaml"

echo
echo "=== TRACK B: payload activate ==="
rm -rf "$PLUGIN_TARGET"
mkdir -p "$PLUGIN_TARGET"
"$PY" "$KIT/payload/cursor_workflow" activate \
  --directory "$PLUGIN_TARGET" \
  --source "$KIT/payload"
"$PLUGIN_TARGET/.venv/bin/python" -m cursor_workflow gates --directory "$PLUGIN_TARGET"
"$PY" .ai_infra/scripts/architecture/check_consumer_purity.py --target "$PLUGIN_TARGET"

echo
echo "=== SMOKE PASS ==="
echo "SMOKE=$SMOKE"
echo "PLUGIN_TARGET=$PLUGIN_TARGET"
echo "Note: contributors validate may FAIL until user_settings placeholders are replaced (expected)."
