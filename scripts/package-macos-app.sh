#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h:h}"
APP="$ROOT/dist/MERRICK.app"
STAGE="$ROOT/dist/MERRICK-installer"
DMG="$ROOT/dist/MERRICK-macOS-arm64.dmg"
PUBLIC_RELEASE="${JARVIS_PUBLIC_RELEASE:-0}"
SIGN_IDENTITY="${JARVIS_CODESIGN_IDENTITY:--}"
NOTARY_PROFILE="${JARVIS_NOTARY_PROFILE:-}"

if [[ "$PUBLIC_RELEASE" != "0" && "$PUBLIC_RELEASE" != "1" ]]; then
  print -u2 "JARVIS_PUBLIC_RELEASE must be 0 or 1."
  exit 64
fi
if [[ "$PUBLIC_RELEASE" == "1" ]]; then
  if [[ -z "$SIGN_IDENTITY" || "$SIGN_IDENTITY" == "-" ]]; then
    print -u2 "Public release requires JARVIS_CODESIGN_IDENTITY with a Developer ID Application identity."
    exit 1
  fi
  if [[ -z "$NOTARY_PROFILE" ]]; then
    print -u2 "Public release requires a notarytool keychain profile in JARVIS_NOTARY_PROFILE."
    exit 1
  fi
  if ! /usr/bin/security find-identity -v -p codesigning | /usr/bin/grep -Fq \""$SIGN_IDENTITY"\"; then
    print -u2 "The requested Developer ID signing identity is not available in this keychain."
    exit 1
  fi
  # Validate upload credentials before spending time on a release build.
  /usr/bin/xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" \
    --output-format json >/dev/null
fi

"$ROOT/scripts/build-macos-app.sh"
"$ROOT/scripts/verify-macos-release.sh" "$APP"

# Fail before producing an image if the recipient would receive an incomplete
# or invalid bundle.  This keeps the Finder drag-to-Applications flow honest:
# no developer checkout is required to diagnose a missing runtime later.
test -x "$APP/Contents/MacOS/Merrick"
test -d "$APP/Contents/Resources/runtime"
plutil -lint "$APP/Contents/Info.plist" >/dev/null
codesign --verify --deep --strict --verbose=2 "$APP"

rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE"
/usr/bin/ditto "$APP" "$STAGE/MERRICK.app"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "MERRICK" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
# The staging copy is only an input to hdiutil. Leaving it behind registers a
# second Finder-launchable bundle and was the source of duplicate local cores.
rm -rf "$STAGE"

if [[ "$PUBLIC_RELEASE" == "1" ]]; then
  codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DMG"
  NOTARY_RESULT="$ROOT/dist/MERRICK-notarization.json"
  NOTARY_LOG="$ROOT/dist/MERRICK-notarization-log.json"
  /usr/bin/xcrun notarytool submit "$DMG" \
    --keychain-profile "$NOTARY_PROFILE" --wait --output-format json >"$NOTARY_RESULT"
  NOTARY_ID=$("$ROOT/.venv/bin/python" -c \
    'import json, sys; print(json.load(open(sys.argv[1]))["id"])' "$NOTARY_RESULT")
  /usr/bin/xcrun notarytool log "$NOTARY_ID" \
    --keychain-profile "$NOTARY_PROFILE" "$NOTARY_LOG"
  "$ROOT/.venv/bin/python" -c \
    'import json, sys; result=json.load(open(sys.argv[1])); status=result.get("status"); sys.exit(0 if status == "Accepted" else f"Apple notarization status: {status}; inspect MERRICK-notarization-log.json")' \
    "$NOTARY_RESULT"
  /usr/bin/xcrun stapler staple "$DMG"
  /usr/bin/xcrun stapler validate "$DMG"
  /usr/sbin/spctl --assess --type open \
    --context context:primary-signature --verbose=2 "$DMG"
else
  print -u2 "Built an internal ad-hoc-signed QA image. Set JARVIS_PUBLIC_RELEASE=1 with Developer ID and notarization credentials before external distribution."
fi
echo "$DMG"
