#!/bin/sh

set -eu
. "$(dirname -- "$0")/openclaw-common.sh"

cd "$JARVIS_PROJECT_ROOT"
NODE_BIN="$NODE_BIN_DIR/node"
OPENCLAW_CLI="$JARVIS_PROJECT_ROOT/node_modules/openclaw/openclaw.mjs"
BUNDLED_CODEX_MANIFEST="$JARVIS_PROJECT_ROOT/node_modules/openclaw/dist/extensions/codex/openclaw.plugin.json"

test -x "$NODE_BIN"
test -r "$OPENCLAW_CLI"
test -r "$BUNDLED_CODEX_MANIFEST"

# Old MERRICK builds registered @openclaw/codex as a path/global plugin. That
# stale record shadows the signed bundled copy and loses access to OpenClaw's
# OAuth store. Keep its files (they live inside the immutable app bundle) but
# remove the obsolete record and config selection. setup-openclaw.sh restores
# the complete application-owned config immediately after this command.
"$NODE_BIN" "$OPENCLAW_CLI" plugins uninstall codex --force --keep-files

# The old auto-installer may also have left one or more generated npm project
# copies. They are executable plugin caches, not OAuth/session data, and would
# still shadow the bundled provider even after its install record is removed.
CODEX_PROJECTS_ROOT="$OPENCLAW_STATE_DIR/npm/projects"
if [ -d "$CODEX_PROJECTS_ROOT" ]; then
  for CODEX_PROJECT in "$CODEX_PROJECTS_ROOT"/openclaw-codex-*; do
    test -d "$CODEX_PROJECT" || continue
    CODEX_PACKAGE="$CODEX_PROJECT/node_modules/@openclaw/codex/package.json"
    CODEX_MANIFEST="$CODEX_PROJECT/node_modules/@openclaw/codex/openclaw.plugin.json"
    if "$NODE_BIN" -e '
      const fs = require("node:fs");
      const pkg = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
      const manifest = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
      if (pkg.name !== "@openclaw/codex" || manifest.id !== "codex") process.exit(1);
    ' "$CODEX_PACKAGE" "$CODEX_MANIFEST"; then
      /usr/bin/find "$CODEX_PROJECT" -depth -delete
    else
      echo "Refusing to remove an unverified OpenClaw plugin project: $CODEX_PROJECT" >&2
      exit 1
    fi
  done
fi

"$NODE_BIN" "$OPENCLAW_CLI" plugins registry --refresh --json >/dev/null
