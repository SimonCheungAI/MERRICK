#!/bin/zsh
set -euo pipefail

if (( $# != 1 )); then
  print -u2 "Usage: verify-macos-release.sh /path/to/MERRICK.app"
  exit 64
fi

APP_PATH=${1:A}
CONTENTS="$APP_PATH/Contents"
RUNTIME="$CONTENTS/Resources/runtime"

test -d "$APP_PATH"
test -x "$CONTENTS/MacOS/Merrick"
test -d "$RUNTIME"
test -x "$RUNTIME/.venv/bin/python"
test -x "$RUNTIME/node/bin/node"
test -x "$RUNTIME/node_modules/.pnpm/node_modules/@openai/codex/bin/codex.js"
test -f "$RUNTIME/node_modules/openclaw/dist/extensions/codex/openclaw.plugin.json"
test -f "$RUNTIME/server/main.py"
test -f "$RUNTIME/server/openclaw_client.py"
test -f "$RUNTIME/server/runtime_contract_generated.py"
test -f "$RUNTIME/web/index.html"
test -f "$RUNTIME/web/app.js"
test -f "$RUNTIME/web/runtime-contract.generated.js"
test -f "$RUNTIME/config/runtime-contract.json"
test -f "$RUNTIME/scripts/runtime-contract.generated.sh"
test -f "$RUNTIME/scripts/run-openclaw-gateway.sh"
test -f "$RUNTIME/scripts/setup-openclaw.sh"
test -x "$RUNTIME/scripts/migrate-openclaw-codex-plugin.sh"
test -f "$RUNTIME/scripts/uninstall-merrick.sh"
test -f "$RUNTIME/package.json"
test -f "$RUNTIME/pnpm-lock.yaml"
test -f "$RUNTIME/pnpm-workspace.yaml"
test -f "$RUNTIME/voice/steadfast-reference.wav"
test -f "$RUNTIME/voice/steadfast-reference-en.wav"

/usr/bin/plutil -lint "$CONTENTS/Info.plist" >/dev/null
/usr/bin/codesign --verify --deep --strict --verbose=2 "$APP_PATH"
/usr/bin/file "$CONTENTS/MacOS/Merrick" | /usr/bin/grep -q "arm64"

PYTHONDONTWRITEBYTECODE=1 "$RUNTIME/.venv/bin/python" -I -B -c \
  'import fastapi, httpx, uvicorn; print("python-runtime-ok")' >/dev/null
"$RUNTIME/node/bin/node" --version >/dev/null
/bin/zsh -n "$RUNTIME/scripts/run-openclaw-gateway.sh"
/bin/zsh -n "$RUNTIME/scripts/setup-openclaw.sh"
/bin/zsh -n "$RUNTIME/scripts/migrate-openclaw-codex-plugin.sh"
/bin/zsh -n "$RUNTIME/scripts/uninstall-merrick.sh"

. "$RUNTIME/scripts/runtime-contract.generated.sh"
JARVIS_SELECTED_PROVIDER=$JARVIS_DEFAULT_PROVIDER
JARVIS_SELECTED_MODEL=$JARVIS_DEFAULT_MODEL
JARVIS_SELECTED_BASE_URL=""
merrick_apply_provider_contract

# Exercise the actual clean-install setup path in an isolated temporary state
# directory. This catches a bundle which looks complete but cannot initialise
# OpenClaw without a developer checkout or a package-manager download.
VERIFY_STATE=$(/usr/bin/mktemp -d /tmp/jarvis-release-verify.XXXXXX)
trap '/usr/bin/find "$VERIFY_STATE" -depth -delete >/dev/null 2>&1 || true' EXIT
OPENCLAW_STATE_DIR="$VERIFY_STATE/OpenClaw" \
OPENCLAW_CONFIG_PATH="$VERIFY_STATE/OpenClaw/openclaw.json" \
OPENCLAW_TOKEN_FILE="$VERIFY_STATE/OpenClaw/.gateway-token" \
OPENCLAW_ACTION_SECRET_FILE="$VERIFY_STATE/OpenClaw/.action-secret" \
JARVIS_WORKSPACE_DIR="$VERIFY_STATE/Workspace/Documents" \
NODE_BIN_DIR="$RUNTIME/node/bin" \
JARVIS_SELECTED_PROVIDER="$JARVIS_DEFAULT_PROVIDER" \
JARVIS_SELECTED_MODEL="$JARVIS_DEFAULT_MODEL" \
JARVIS_MODEL_API_KEY=unused \
  "$RUNTIME/scripts/setup-openclaw.sh" >"$VERIFY_STATE/setup.log" 2>&1

OPENCLAW_STATE_DIR="$VERIFY_STATE/OpenClaw" \
OPENCLAW_CONFIG_PATH="$VERIFY_STATE/OpenClaw/openclaw.json" \
JARVIS_PROJECT_ROOT="$RUNTIME" \
JARVIS_WORKSPACE_DIR="$VERIFY_STATE/Workspace/Documents" \
JARVIS_MAIN_MODEL="$JARVIS_MAIN_MODEL" \
JARVIS_CONVERSATION_MODEL="$JARVIS_CONVERSATION_MODEL" \
JARVIS_SELECTED_MODEL="$JARVIS_SELECTED_MODEL" \
JARVIS_SELECTED_BASE_URL="$JARVIS_SELECTED_BASE_URL" \
JARVIS_OPENAI_RUNTIME="$JARVIS_OPENAI_RUNTIME" \
JARVIS_ANTHROPIC_RUNTIME="$JARVIS_ANTHROPIC_RUNTIME" \
JARVIS_OPENCLAW_PUBLIC_ORIGIN="http://127.0.0.1:$OPENCLAW_DEFAULT_PORT" \
JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH="$RUNTIME/openclaw/codex-computer-use-marketplace" \
  "$RUNTIME/node/bin/node" "$RUNTIME/node_modules/openclaw/openclaw.mjs" \
    plugins inspect codex --runtime --json >"$VERIFY_STATE/codex-runtime.json" 2>&1

"$RUNTIME/.venv/bin/python" -I -B -c \
  'import json, sys; plugin=json.load(open(sys.argv[1], encoding="utf-8"))["plugin"]; assert plugin["origin"] == "bundled"; assert plugin["status"] == "loaded"' \
  "$VERIFY_STATE/codex-runtime.json"

if /usr/bin/grep -E \
  "ERR_PNPM_NO_PKG_MANIFEST|plugin not installed: codex|unknown web_search provider: codex|openKeyedStore is only available for trusted plugins|spawn npm" \
  "$VERIFY_STATE/setup.log" "$VERIFY_STATE/codex-runtime.json" >/dev/null; then
  print -u2 "The bundled OpenClaw clean-install setup is incomplete."
  /usr/bin/tail -n 20 "$VERIFY_STATE/setup.log" >&2
  exit 1
fi

print "Verified release runtime: $APP_PATH"
