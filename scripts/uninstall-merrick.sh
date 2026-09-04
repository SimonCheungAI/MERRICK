#!/bin/zsh
set -u

# This script is copied to a private temporary path and launched only after the
# user confirms the destructive uninstall in the native MERRICK dialog.
EXPECTED_BUNDLE_ID="ai.jarvis.desktop"
KEYCHAIN_SERVICE="ai.jarvis.desktop.provider-credentials"
SIGKILL=9

APP_PATH=""
PARENT_PID=""
while (( $# > 0 )); do
  case "$1" in
    --app)
      APP_PATH=${2:-}
      shift 2
      ;;
    --parent-pid)
      PARENT_PID=${2:-}
      shift 2
      ;;
    *)
      exit 64
      ;;
  esac
done

if [[ -z "$APP_PATH" || -z "$PARENT_PID" || "$PARENT_PID" != <-> ]]; then
  exit 64
fi
if [[ "$APP_PATH" == "/" || "$APP_PATH" != *.app ]]; then
  exit 64
fi
INFO_PLIST="$APP_PATH/Contents/Info.plist"
BUNDLE_ID=$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "$INFO_PLIST" 2>/dev/null)
if [[ "$BUNDLE_ID" != "$EXPECTED_BUNDLE_ID" ]]; then
  exit 65
fi

# Let the native host perform its graceful bounded shutdown first.
for _ in {1..120}; do
  /bin/kill -0 "$PARENT_PID" 2>/dev/null || break
  /bin/sleep 0.1
done

CURRENT_UID=$(/usr/bin/id -u)
APP_PATH=${APP_PATH:A}
RUNTIME_PATH="$APP_PATH/Contents/Resources/runtime"
PRIVATE_CONFIG="$HOME/Library/Application Support/JarvisStark/OpenClaw/openclaw.json"
PID_LIST=$(/usr/bin/mktemp /tmp/jarvis-uninstall-pids.XXXXXX) || exit 70
trap '/bin/rm -f "$PID_LIST"' EXIT

# A saved PID or a command-line substring is only a candidate, never proof of
# ownership. Match the live executable; renamed Gateways also need this exact
# runtime cwd and private config, as in the backend's ownership verifier.
is_owned_process() {
  local pid=$1 process_uid process_command row open_files line descriptor=""
  local bundled_executable=false runtime_cwd=false private_config=false bundled_node=false
  [[ "$pid" == <-> ]] && (( pid > 1 )) || return 1
  row=$(/bin/ps -p "$pid" -o uid= -o command= 2>/dev/null) || return 1
  read -r process_uid process_command <<< "$row"
  [[ "$process_uid" == "$CURRENT_UID" ]] || return 1
  open_files=$(/usr/sbin/lsof -nP -a -p "$pid" -Ffn 2>/dev/null) || return 1
  for line in "${(@f)open_files}"; do
    case "$line" in
      f*) descriptor=${line#f} ;;
      n*)
        local file_path=${line#n}
        [[ "$descriptor" == txt && "$file_path" == "$APP_PATH/Contents/"* ]] && bundled_executable=true
        [[ "$descriptor" == txt && "$file_path" == "$RUNTIME_PATH/node/bin/node" ]] && bundled_node=true
        [[ "$descriptor" == cwd && "$file_path" == "$RUNTIME_PATH" ]] && runtime_cwd=true
        [[ "$file_path" == "$PRIVATE_CONFIG" ]] && private_config=true
        ;;
    esac
  done
  if [[ "$process_command" == openclaw || "$process_command" == openclaw-gateway ||
        "$process_command" == *"/openclaw.mjs"*"gateway run"* ]]; then
    $bundled_node && $runtime_cwd && $private_config
  else
    # Merely mentioning our bundle as an argument does not make a process ours.
    [[ "$process_command" == "$APP_PATH/Contents/"* ]] && $bundled_executable
  fi
}

capture_owned_process() {
  local pid=$1 started
  is_owned_process "$pid" || return 0
  started=$(/bin/ps -p "$pid" -o lstart= 2>/dev/null) || return 0
  [[ -n "$started" ]] && print -r -- "$pid|$started" >> "$PID_LIST"
  return 0
}

still_owned_process() {
  local pid=$1 started=$2 current_start
  current_start=$(/bin/ps -p "$pid" -o lstart= 2>/dev/null) || return 1
  [[ -n "$started" && "$current_start" == "$started" ]] && is_owned_process "$pid"
}

/bin/ps -axo pid=,uid=,command= | while read -r candidate_pid candidate_uid candidate_command; do
  [[ "$candidate_pid" == <-> && "$candidate_uid" == "$CURRENT_UID" ]] || continue
  [[ "$candidate_command" == *"$APP_PATH/Contents/"* ]] || continue
  capture_owned_process "$candidate_pid"
done

# OpenClaw intentionally has a short process title. The owner record only
# identifies a candidate; a stale PID belonging to another installation fails
# the same live ownership check as every other candidate.
OWNER_RECORD="$HOME/Library/Application Support/JarvisStark/OpenClaw/.gateway-owner.json"
if [[ -f "$OWNER_RECORD" ]]; then
  OWNER_PID=$(/usr/bin/sed -n 's/.*"pid"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$OWNER_RECORD" | /usr/bin/head -n 1)
  [[ "$OWNER_PID" == <-> ]] && capture_owned_process "$OWNER_PID"
fi

/usr/bin/sort -u "$PID_LIST" -o "$PID_LIST"
while IFS='|' read -r owned_pid owned_start; do
  still_owned_process "$owned_pid" "$owned_start" || continue
  /bin/kill -TERM "$owned_pid" 2>/dev/null || true
done < "$PID_LIST"
for _ in {1..20}; do
  any_running=false
  while IFS='|' read -r owned_pid owned_start; do
    still_owned_process "$owned_pid" "$owned_start" || continue
    if /bin/kill -0 "$owned_pid" 2>/dev/null; then any_running=true; fi
  done < "$PID_LIST"
  $any_running || break
  /bin/sleep 0.1
done
while IFS='|' read -r owned_pid owned_start; do
  still_owned_process "$owned_pid" "$owned_start" || continue
  if /bin/kill -0 "$owned_pid" 2>/dev/null; then
    /bin/kill -"$SIGKILL" "$owned_pid" 2>/dev/null || true
  fi
done < "$PID_LIST"

# Delete every credential stored under the app-owned Keychain service.
while /usr/bin/security delete-generic-password -s "$KEYCHAIN_SERVICE" >/dev/null 2>&1; do :; done

# Reset only this bundle's privacy grants; never touch another application's
# microphone, speech, screen-recording, or Apple Events permissions.
for permission in Microphone SpeechRecognition ScreenCapture AppleEvents; do
  /usr/bin/tccutil reset "$permission" "$EXPECTED_BUNDLE_ID" >/dev/null 2>&1 || true
done

/usr/bin/defaults delete "$EXPECTED_BUNDLE_ID" >/dev/null 2>&1 || true
/bin/rm -rf -- \
  "$HOME/Library/Application Support/JarvisStark" \
  "$HOME/Library/Caches/JarvisStark" \
  "$HOME/Library/Caches/$EXPECTED_BUNDLE_ID" \
  "$HOME/Library/HTTPStorages/$EXPECTED_BUNDLE_ID" \
  "$HOME/Library/Saved Application State/$EXPECTED_BUNDLE_ID.savedState" \
  "$HOME/Library/WebKit/$EXPECTED_BUNDLE_ID" \
  "$HOME/Library/Preferences/$EXPECTED_BUNDLE_ID.plist"

# macOS keeps a small per-executable CrashReporter registration outside the
# app's normal data directory. Remove only MERRICK's exact legacy prefix;
# unrelated diagnostic reports and other applications are intentionally kept.
CRASH_REPORTER_DIRECTORY="$HOME/Library/Application Support/CrashReporter"
if [[ -d "$CRASH_REPORTER_DIRECTORY" ]]; then
  /usr/bin/find "$CRASH_REPORTER_DIRECTORY" -maxdepth 1 -type f -name 'Jarvis_*.plist' -delete
fi
/bin/rm -f -- /tmp/jarvis-debug.log /tmp/jarvis-native.log
/bin/rm -rf -- "$APP_PATH"

if [[ -e "$APP_PATH" ]]; then
  /usr/bin/osascript -e 'display dialog "MERRICK data was removed, but macOS did not allow the application itself to be deleted. Move it from Applications to the Bin." buttons {"OK"} default button "OK" with icon caution' >/dev/null 2>&1 || true
  exit 73
fi

/usr/bin/osascript -e 'display notification "MERRICK and its local data were removed." with title "Uninstall complete"' >/dev/null 2>&1 || true
/bin/rm -f -- "$0" "$PID_LIST"
trap - EXIT
