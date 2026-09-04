#!/bin/sh

set -eu

JARVIS_PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$(dirname -- "$0")/runtime-contract.generated.sh"
OPENCLAW_STATE_DIR=${OPENCLAW_STATE_DIR:-"$HOME/Library/Application Support/JarvisStark/OpenClaw"}
OPENCLAW_CONFIG_PATH=${OPENCLAW_CONFIG_PATH:-"$OPENCLAW_STATE_DIR/openclaw.json"}
OPENCLAW_TOKEN_FILE=${OPENCLAW_TOKEN_FILE:-"$OPENCLAW_STATE_DIR/.gateway-token"}
OPENCLAW_ACTION_SECRET_FILE=${OPENCLAW_ACTION_SECRET_FILE:-"$OPENCLAW_STATE_DIR/.action-secret"}
OPENCLAW_PORT=${OPENCLAW_PORT:-$OPENCLAW_DEFAULT_PORT}
# OpenClaw emits canonical Control UI links for visible child sessions only
# when its public origin is known. The desktop backend supplies its random
# owner port; direct setup/diagnostic calls use the pinned loopback default.
JARVIS_OPENCLAW_PUBLIC_ORIGIN=${JARVIS_OPENCLAW_PUBLIC_ORIGIN:-"http://127.0.0.1:$OPENCLAW_PORT"}
# Keep user-created voice-task files separate from the operational files that
# support MERRICK itself. This is the only directory exposed to Codex's
# workspace-write sandbox.
JARVIS_WORKSPACE_DIR=${JARVIS_WORKSPACE_DIR:-"$HOME/Library/Application Support/JarvisStark/Workspace/Documents"}
# Diagnostics and setup load the same app-owned Computer Use marketplace as
# the live backend. Without this export `openclaw config validate` incorrectly
# reports the capability as unavailable even though runtime startup injects it.
JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH=${JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH:-"$JARVIS_PROJECT_ROOT/openclaw/codex-computer-use-marketplace"}

if command -v pnpm >/dev/null 2>&1; then
  PNPM_BIN=$(command -v pnpm)
else
  PNPM_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm"
fi

# A release build embeds Node at runtime/node. Developers can still use the
# Codex-managed Node cache when running directly from the source checkout.
if [ -z "${NODE_BIN_DIR:-}" ] && [ -x "$JARVIS_PROJECT_ROOT/node/bin/node" ]; then
  NODE_BIN_DIR="$JARVIS_PROJECT_ROOT/node/bin"
else
  NODE_BIN_DIR=${NODE_BIN_DIR:-"$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"}
fi
# Recent OpenClaw launchers may invoke the project-local npm shim while
# resolving their bundled runtime.  A release bundle carries npm under its
# copied node_modules tree, not beside the standalone Node binary, so expose
# that shim before starting the Gateway.
PATH="$NODE_BIN_DIR:$JARVIS_PROJECT_ROOT/node_modules/.bin:$(dirname "$PNPM_BIN"):$PATH"

# The desktop gateway starts OpenClaw through its embedded Node executable and
# never invokes pnpm.  Keeping this check opt-in means a distributed MERRICK
# app can launch on a clean Mac without a Codex development runtime installed.
# Setup, diagnostics, and the visible OAuth recovery flow call it explicitly.
require_pnpm() {
  if [ ! -x "$PNPM_BIN" ]; then
    echo "pnpm was not found. Open this project in Codex once, or install pnpm 11." >&2
    exit 1
  fi
}

# The native MERRICK host owns provider credentials in macOS Keychain and only
# injects an API key into its direct backend child.  This launcher receives the
# selected provider metadata, never persists a key, and gives OpenClaw a stable
# model reference for this one gateway process.
JARVIS_SELECTED_PROVIDER=${JARVIS_SELECTED_PROVIDER:-$JARVIS_DEFAULT_PROVIDER}
JARVIS_SELECTED_MODEL=${JARVIS_SELECTED_MODEL:-$JARVIS_DEFAULT_MODEL}
JARVIS_SELECTED_BASE_URL=${JARVIS_SELECTED_BASE_URL:-}
JARVIS_MODEL_API_KEY=${JARVIS_MODEL_API_KEY:-unused}
merrick_apply_provider_contract

export PATH JARVIS_PROJECT_ROOT OPENCLAW_STATE_DIR OPENCLAW_CONFIG_PATH JARVIS_WORKSPACE_DIR \
  OPENCLAW_PORT JARVIS_OPENCLAW_PUBLIC_ORIGIN \
  JARVIS_SELECTED_PROVIDER JARVIS_SELECTED_MODEL JARVIS_SELECTED_BASE_URL JARVIS_MODEL_API_KEY \
  JARVIS_MAIN_MODEL JARVIS_CONVERSATION_MODEL JARVIS_OPENAI_RUNTIME JARVIS_ANTHROPIC_RUNTIME \
  JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH

load_openclaw_token() {
  if [ ! -r "$OPENCLAW_TOKEN_FILE" ]; then
    echo "OpenClaw token is missing. Run scripts/setup-openclaw.sh first." >&2
    exit 1
  fi
  OPENCLAW_GATEWAY_TOKEN=$(tr -d '\r\n' < "$OPENCLAW_TOKEN_FILE")
  export OPENCLAW_GATEWAY_TOKEN
}

load_openclaw_action_secret() {
  if [ ! -r "$OPENCLAW_ACTION_SECRET_FILE" ]; then
    echo "OpenClaw action secret is missing. Run scripts/setup-openclaw.sh first." >&2
    exit 1
  fi
  JARVIS_ACTION_SECRET=$(tr -d '\r\n' < "$OPENCLAW_ACTION_SECRET_FILE")
  export JARVIS_ACTION_SECRET
}
