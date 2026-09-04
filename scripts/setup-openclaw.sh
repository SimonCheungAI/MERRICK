#!/bin/sh

set -eu
. "$(dirname -- "$0")/openclaw-common.sh"

cd "$JARVIS_PROJECT_ROOT"
NODE_BIN="$NODE_BIN_DIR/node"
OPENCLAW_CLI="$JARVIS_PROJECT_ROOT/node_modules/openclaw/openclaw.mjs"
JARVIS_BUNDLED_RUNTIME=0
if [ -x "$JARVIS_PROJECT_ROOT/node/bin/node" ] && [ -r "$OPENCLAW_CLI" ]; then
  JARVIS_BUNDLED_RUNTIME=1
fi

if [ "$JARVIS_BUNDLED_RUNTIME" = "1" ]; then
  # A signed release already contains the frozen dependency tree and compiled
  # safe-tools plugin. Never mutate that sealed bundle or require pnpm/network
  # access on the user's Mac during first launch.
  test -r "$JARVIS_PROJECT_ROOT/openclaw/plugins/jarvis-safe-tools/dist/index.js"
else
  require_pnpm
  "$PNPM_BIN" install --frozen-lockfile
  "$PNPM_BIN" --filter openclaw-plugin-jarvis-safe-tools run build

  # OpenClaw 2026.8 ships the official Codex provider as a separately pinned
  # package. Development checkouts stage that exact package into OpenClaw's
  # bundled extension tree, matching the signed-app build and preserving the
  # provider's trusted credential-store access without a global/path install.
  CODEX_PROVIDER_PACKAGE="$JARVIS_PROJECT_ROOT/node_modules/@openclaw/codex"
  BUNDLED_CODEX_DIR="$JARVIS_PROJECT_ROOT/node_modules/openclaw/dist/extensions/codex"
  test -r "$CODEX_PROVIDER_PACKAGE/openclaw.plugin.json"
  test -r "$CODEX_PROVIDER_PACKAGE/dist/index.js"
  if [ -d "$BUNDLED_CODEX_DIR" ]; then
    /usr/bin/find "$BUNDLED_CODEX_DIR" -depth -delete
  fi
  /usr/bin/ditto "$CODEX_PROVIDER_PACKAGE" "$BUNDLED_CODEX_DIR"
fi

umask 077
mkdir -p "$OPENCLAW_STATE_DIR" "$OPENCLAW_STATE_DIR/workspace" \
  "$OPENCLAW_STATE_DIR/memory-writer-workspace" \
  "$OPENCLAW_STATE_DIR/action-planner-workspace" "$OPENCLAW_STATE_DIR/memory"
mkdir -p "$JARVIS_WORKSPACE_DIR"
chmod 700 "$OPENCLAW_STATE_DIR" "$OPENCLAW_STATE_DIR/workspace" \
  "$OPENCLAW_STATE_DIR/memory-writer-workspace" \
  "$OPENCLAW_STATE_DIR/action-planner-workspace" "$OPENCLAW_STATE_DIR/memory"
chmod 700 "$JARVIS_WORKSPACE_DIR"

if [ ! -s "$OPENCLAW_TOKEN_FILE" ]; then
  /usr/bin/openssl rand -hex 32 > "$OPENCLAW_TOKEN_FILE"
fi
chmod 600 "$OPENCLAW_TOKEN_FILE"

if [ ! -s "$OPENCLAW_ACTION_SECRET_FILE" ]; then
  /usr/bin/openssl rand -hex 32 > "$OPENCLAW_ACTION_SECRET_FILE"
fi
chmod 600 "$OPENCLAW_ACTION_SECRET_FILE"

/usr/bin/install -m 600 openclaw/openclaw.template.json5 "$OPENCLAW_CONFIG_PATH"
/usr/bin/install -m 600 openclaw/workspace/AGENTS.md "$OPENCLAW_STATE_DIR/workspace/AGENTS.md"
/usr/bin/install -m 600 openclaw/workspace/IDENTITY.md "$OPENCLAW_STATE_DIR/workspace/IDENTITY.md"
/usr/bin/install -m 600 openclaw/workspace/SOUL.md "$OPENCLAW_STATE_DIR/workspace/SOUL.md"
/usr/bin/install -m 600 openclaw/action-planner-workspace/AGENTS.md \
  "$OPENCLAW_STATE_DIR/action-planner-workspace/AGENTS.md"
/usr/bin/install -m 600 openclaw/action-planner-workspace/IDENTITY.md \
  "$OPENCLAW_STATE_DIR/action-planner-workspace/IDENTITY.md"
/usr/bin/install -m 600 openclaw/action-planner-workspace/SOUL.md \
  "$OPENCLAW_STATE_DIR/action-planner-workspace/SOUL.md"

load_openclaw_token
load_openclaw_action_secret
if [ "$JARVIS_BUNDLED_RUNTIME" = "1" ]; then
  "$NODE_BIN" "$OPENCLAW_CLI" config validate
else
  "$PNPM_BIN" exec openclaw config validate
fi

echo "OpenClaw is installed and its MERRICK companion config is valid."
echo "State: $OPENCLAW_STATE_DIR"
