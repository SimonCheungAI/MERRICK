#!/bin/sh

set -eu
. "$(dirname -- "$0")/openclaw-common.sh"
require_pnpm
load_openclaw_token

cd "$JARVIS_PROJECT_ROOT"
# This is the visible recovery path used when a browser/device-code consent
# needs user interaction. It writes only to MERRICK's OpenClaw agent store.
exec "$PNPM_BIN" exec openclaw models auth --agent main login \
  --provider "$JARVIS_DEFAULT_PROBE_ROUTE" \
  --profile-id "$JARVIS_DEFAULT_PROBE_PROFILE_ID" \
  --device-code
