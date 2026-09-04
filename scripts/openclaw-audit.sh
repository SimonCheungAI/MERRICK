#!/bin/sh

set -eu
. "$(dirname -- "$0")/openclaw-common.sh"
require_pnpm
load_openclaw_token

cd "$JARVIS_PROJECT_ROOT"
"$PNPM_BIN" exec openclaw config validate
"$PNPM_BIN" exec openclaw plugins inspect jarvis-safe-tools --runtime --json
"$PNPM_BIN" exec openclaw security audit --deep
