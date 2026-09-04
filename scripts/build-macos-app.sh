#!/bin/zsh
set -euo pipefail

# Build a self-contained, Apple-silicon MERRICK application. The release
# carries its local Python backend, OpenClaw runtime and Node binary inside the
# bundle; it never carries personal state, API keys, OAuth tokens or memories.
ROOT="${0:A:h:h}"
FINAL_APP="$ROOT/dist/MERRICK.app"
APP="$ROOT/dist/MERRICK.app.building"
CONTENTS="$APP/Contents"
RUNTIME="$CONTENTS/Resources/runtime"
UV_PYTHON="$HOME/.local/share/uv/python/cpython-3.14-macos-aarch64-none"
VOICE_UV_PYTHON="${HOME}/.local/share/uv/python/cpython-3.12-macos-aarch64-none"
VOICE_ENV="$ROOT/artifacts/voice-design/.venv"
VOICE_MODEL_CACHE="$ROOT/artifacts/voice-design/hf-cache/hub/models--mlx-community--Qwen3-TTS-12Hz-1.7B-Base-8bit"
VOICE_REFERENCE="$ROOT/artifacts/voice-design/samples/01-jarvis-steadfast.wav"
VOICE_ENGLISH_REFERENCE="$ROOT/artifacts/voice-design/samples/04-steadfast-english-identity.wav"
VOICE_SPEC="$ROOT/artifacts/voice-design/voice-design-spec.json"
NODE_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
COMPUTER_USE_CLIENT="$HOME/.codex/computer-use"
COMPUTER_USE_PLUGIN="$HOME/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use"
COMPUTER_USE_MARKETPLACE="$ROOT/openclaw/codex-computer-use-marketplace"
CODEX_PROVIDER_PLUGIN="$ROOT/node_modules/@openclaw/codex"
CODESIGN_IDENTITY="${JARVIS_CODESIGN_IDENTITY:--}"

if [[ ! -x "$ROOT/.venv/bin/python" || ! -d "$ROOT/node_modules/openclaw" ]]; then
  print -u2 "Local Python or OpenClaw dependencies are missing. Run scripts/setup-openclaw.sh first."
  exit 1
fi
if [[ ! -x "$UV_PYTHON/bin/python3.14" || ! -x "$NODE_BIN" ]]; then
  print -u2 "The bundled Python or Node runtime is missing on this build machine."
  exit 1
fi
if [[ ! -x "$VOICE_ENV/bin/python" || ! -x "$VOICE_UV_PYTHON/bin/python3.12" || ! -d "$VOICE_MODEL_CACHE" || ! -f "$VOICE_REFERENCE" || ! -f "$VOICE_ENGLISH_REFERENCE" || ! -f "$VOICE_SPEC" ]]; then
  print -u2 "The selected Steadfast voice runtime or model is missing on this build machine."
  exit 1
fi
if [[ ! -x "$COMPUTER_USE_CLIENT/Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient" || ! -f "$COMPUTER_USE_PLUGIN/.codex-plugin/plugin.json" || ! -f "$COMPUTER_USE_MARKETPLACE/.agents/plugins/marketplace.json" ]]; then
  print -u2 "The official Codex Computer Use assets are missing on this build machine."
  exit 1
fi
if [[ ! -f "$CODEX_PROVIDER_PLUGIN/openclaw.plugin.json" || ! -f "$CODEX_PROVIDER_PLUGIN/dist/index.js" ]]; then
  print -u2 "The pinned official Codex provider plugin is missing on this build machine."
  exit 1
fi

"$ROOT/.venv/bin/python" "$ROOT/scripts/verify-provider-bindings.py" "$ROOT"
"$ROOT/.venv/bin/python" "$ROOT/scripts/generate-runtime-contract.py" --check "$ROOT"

# Coexistence is a release gate: never build an app whose cleanup can target
# another installation or whose launch environment can borrow its state.
"$ROOT/.venv/bin/python" "$ROOT/tests/test_uninstall_process_ownership.py" -q
"$ROOT/.venv/bin/python" "$ROOT/tests/test_native_runtime_ownership.py" -q
"$ROOT/.venv/bin/python" "$ROOT/tests/test_gateway_identity.py" -q

rm -rf "$APP"
mkdir -p "$CONTENTS/MacOS" "$RUNTIME"

swiftc "$ROOT/desktop/RuntimeContract.generated.swift" \
  "$ROOT/desktop/ProviderLoginParser.swift" \
  "$ROOT/desktop/ProviderConnectionValidation.swift" \
  "$ROOT/desktop/MerrickApp.swift" \
  -o "$CONTENTS/MacOS/Merrick" \
  -framework AppKit -framework WebKit -framework Speech -framework AVFoundation \
  -framework CoreGraphics -framework ScreenCaptureKit -framework UserNotifications
cp "$ROOT/desktop/Info.plist" "$CONTENTS/Info.plist"
cp "$ROOT/assets/AppIcon.icns" "$CONTENTS/Resources/AppIcon.icns"

# Only application code and runtime dependencies enter the bundle. User data
# belongs under ~/Library/Application Support/JarvisStark and is deliberately
# excluded, so sharing the app cannot leak memories, credentials or voiceprint.
for runtimePath in config server web scripts openclaw node_modules; do
  /usr/bin/ditto "$ROOT/$runtimePath" "$RUNTIME/$runtimePath"
done
# OpenClaw grants credential-store access only to bundled or catalog-verified
# official plugins. Stage the already pinned Codex package under OpenClaw's
# sealed bundled tree so OAuth works offline without an npm install and without
# weakening the host trust boundary with a generic load path.
mkdir -p "$RUNTIME/node_modules/openclaw/dist/extensions"
/usr/bin/ditto "${CODEX_PROVIDER_PLUGIN:A}" \
  "$RUNTIME/node_modules/openclaw/dist/extensions/codex"
# Keep the pinned package graph alongside node_modules. The installed runtime
# does not fetch packages, but OpenClaw and release diagnostics still use this
# metadata to identify the exact, auditable dependency set.
for runtimeFile in package.json pnpm-lock.yaml pnpm-workspace.yaml; do
  /usr/bin/ditto "$ROOT/$runtimeFile" "$RUNTIME/$runtimeFile"
done
# pnpm can leave workspace-only links inside node_modules. They point back to
# source-checkout packages that are intentionally absent from a release and
# make strict code-signature verification fail after the bundle is moved.
/usr/bin/find "$RUNTIME/node_modules" -type l ! -exec test -e {} \; -delete
mkdir -p "$RUNTIME/codex-computer-use/marketplace/plugins"
/usr/bin/ditto "$COMPUTER_USE_CLIENT" "$RUNTIME/codex-computer-use/client"
/usr/bin/ditto "$COMPUTER_USE_PLUGIN" "$RUNTIME/codex-computer-use/marketplace/plugins/computer-use"
/usr/bin/ditto "$COMPUTER_USE_MARKETPLACE/.agents" "$RUNTIME/codex-computer-use/marketplace/.agents"
mkdir -p "$RUNTIME/node/bin"
/usr/bin/ditto "$NODE_BIN" "$RUNTIME/node/bin/node"
/usr/bin/ditto "$UV_PYTHON" "$RUNTIME/python"
/usr/bin/ditto "$ROOT/.venv" "$RUNTIME/.venv"

# Steadfast uses an isolated MLX/Python 3.12 runtime and only the selected Base
# cloning model. VoiceDesign prototypes and rejected candidates never enter the
# application bundle.
mkdir -p "$RUNTIME/voice-runtime/model-cache/hub" "$RUNTIME/voice"
/usr/bin/ditto "${VOICE_UV_PYTHON:A}" "$RUNTIME/voice-runtime/python"
/usr/bin/ditto "$VOICE_ENV" "$RUNTIME/voice-runtime/.venv"
/usr/bin/ditto "$VOICE_MODEL_CACHE" "$RUNTIME/voice-runtime/model-cache/hub/${VOICE_MODEL_CACHE:t}"
/usr/bin/ditto "$VOICE_REFERENCE" "$RUNTIME/voice/steadfast-reference.wav"
/usr/bin/ditto "$VOICE_ENGLISH_REFERENCE" "$RUNTIME/voice/steadfast-reference-en.wav"
/usr/bin/ditto "$VOICE_SPEC" "$RUNTIME/voice/voice-design-spec.json"

# The source venv points at a developer-machine Python via absolute symlink.
# Retarget it to the interpreter embedded above. Python resolves the symlink
# before loading stdlib, making the venv portable even if the app is moved.
rm -f "$RUNTIME/.venv/bin/python" "$RUNTIME/.venv/bin/python3" "$RUNTIME/.venv/bin/python3.14"
ln -s ../../python/bin/python3.14 "$RUNTIME/.venv/bin/python"
ln -s python "$RUNTIME/.venv/bin/python3"
ln -s python "$RUNTIME/.venv/bin/python3.14"

# The source voice venv also points to its build-machine interpreter. Retarget
# it to the Python 3.12 runtime placed beside it in the application bundle.
rm -f "$RUNTIME/voice-runtime/.venv/bin/python" "$RUNTIME/voice-runtime/.venv/bin/python3" "$RUNTIME/voice-runtime/.venv/bin/python3.12"
ln -s ../../python/bin/python3.12 "$RUNTIME/voice-runtime/.venv/bin/python"
ln -s python "$RUNTIME/voice-runtime/.venv/bin/python3"
ln -s python "$RUNTIME/voice-runtime/.venv/bin/python3.12"

if [[ -n "$CODESIGN_IDENTITY" && "$CODESIGN_IDENTITY" != "-" ]]; then
  # The release signer applies --options runtime and a secure timestamp to
  # every native dependency before sealing the app, preserving valid vendor
  # signatures and their restricted entitlements. Apple supplies the full
  # Developer ID designated requirement; do not replace it with an ID alone.
  "$ROOT/.venv/bin/python" "$ROOT/scripts/macos_release_signing.py" "$APP" \
    --identity "$CODESIGN_IDENTITY" \
    --report "$ROOT/dist/MERRICK-signing-report.json"
else
  # Local QA remains possible on machines without Apple distribution
  # credentials, but package-macos-app.sh will never mistake this ad-hoc
  # signature for a public release.
  codesign --force --deep --sign - \
    --requirements '=designated => identifier "ai.jarvis.desktop"' "$APP"
fi

# Build away from the live bundle and replace it only after validation. This
# avoids Finder observing a half-written application during long model copies.
rm -rf "$FINAL_APP"
mv "$APP" "$FINAL_APP"
echo "$FINAL_APP"
