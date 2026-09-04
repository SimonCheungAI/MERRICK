#!/bin/sh

set -eu
. "$(dirname -- "$0")/openclaw-common.sh"
load_openclaw_token

OPENCLAW_PORT=${OPENCLAW_PORT:-$OPENCLAW_DEFAULT_PORT}
case "$OPENCLAW_PORT" in
  ''|*[!0-9]*) echo "OPENCLAW_PORT must be numeric." >&2; exit 1 ;;
esac
if [ "$OPENCLAW_PORT" -lt 1024 ] || [ "$OPENCLAW_PORT" -gt 65535 ]; then
  echo "OPENCLAW_PORT is outside the allowed range." >&2
  exit 1
fi

# Never rotate the action key or send a bearer token toward a port already
# owned by another process. The desktop backend performs a second PID check.
if /usr/sbin/lsof -nP -iTCP:"$OPENCLAW_PORT" -sTCP:LISTEN -t 2>/dev/null | grep -q .; then
  echo "Port $OPENCLAW_PORT is already in use; refusing to start or rotate secrets." >&2
  exit 1
fi

# Rotate the action capability key for every Gateway process. Previously used
# capabilities cannot become valid again after an in-memory replay cache reset.
umask 077
ACTION_SECRET_TMP="$OPENCLAW_ACTION_SECRET_FILE.$$"
trap 'rm -f "$ACTION_SECRET_TMP"' EXIT HUP INT TERM
/usr/bin/openssl rand -hex 32 > "$ACTION_SECRET_TMP"
chmod 600 "$ACTION_SECRET_TMP"
mv -f "$ACTION_SECRET_TMP" "$OPENCLAW_ACTION_SECRET_FILE"
trap - EXIT HUP INT TERM
load_openclaw_action_secret

cd "$JARVIS_PROJECT_ROOT"

NODE_BIN="$NODE_BIN_DIR/node"
OPENCLAW_CLI="$JARVIS_PROJECT_ROOT/node_modules/openclaw/openclaw.mjs"
if [ ! -x "$NODE_BIN" ] || [ ! -r "$OPENCLAW_CLI" ]; then
  echo "Pinned OpenClaw runtime is missing. Run scripts/setup-openclaw.sh first." >&2
  exit 1
fi

# MERRICK is the sole supervisor for its bundled Gateway. Prevent the
# child from installing native services, replacing itself, or handing a restart
# to a detached process that the application can no longer shut down.
OPENCLAW_SUPERVISOR_MODE="external"
OPENCLAW_NO_RESPAWN="1"
export OPENCLAW_SUPERVISOR_MODE OPENCLAW_NO_RESPAWN

# Codex app-server enforces workspace-write itself. Wrapping the gateway in
# macOS sandbox-exec prevents that nested sandbox from starting, so native
# Codex edits would fail even inside the allowed workspace. OpenClaw remains
# the authoritative permission and approval layer for host-side operations.
exec "$NODE_BIN" "$OPENCLAW_CLI" gateway run \
  --port "$OPENCLAW_PORT" --bind loopback --auth token
