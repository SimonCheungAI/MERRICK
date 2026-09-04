#!/usr/bin/env bash
set -euo pipefail

DEFAULT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# A source checkout can opt in to its private Git repository.  A packaged app
# has no .git directory and must never create `backups/` inside its signed
# runtime; it writes an equally private local snapshot below Application
# Support instead.
ROOT="${JARVIS_MEMORY_BACKUP_REPOSITORY:-$DEFAULT_ROOT}"
SOURCE="${JARVIS_MEMORY_DIR:-$HOME/Library/Application Support/JarvisStark/OpenClaw/memory}"
if [[ -d "$ROOT/.git" ]]; then
  DESTINATION="$ROOT/backups/jarvis-memory"
  GIT_BACKUP=true
else
  DESTINATION="${JARVIS_MEMORY_BACKUP_DESTINATION:-$HOME/Library/Application Support/JarvisStark/Backups/jarvis-memory}"
  GIT_BACKUP=false
fi
PUBLISH=false
if [[ "${1:-}" == "--publish" ]]; then
  PUBLISH=true
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--publish]" >&2
  exit 2
fi
FILES=(
  jarvis-memory.jsonl
  jarvis-preferences.md
  jarvis-memory-cards.json
  jarvis-memory-revisions.jsonl
  jarvis-memory.db
  jarvis-organizer.db
)

if [[ ! -d "$SOURCE" ]]; then
  echo "MERRICK memory directory was not found: $SOURCE" >&2
  exit 1
fi

mkdir -p "$DESTINATION"
updated=0
for name in "${FILES[@]}"; do
  source_path="$SOURCE/$name"
  [[ -f "$source_path" ]] || continue
  install -m 600 "$source_path" "$DESTINATION/$name"
  updated=$((updated + 1))
done

# Meeting transcripts rotate into one private JSONL file per local hour. Keep
# the hierarchy in the private backup so old meetings never collapse back into
# one large file when MERRICK exits and publishes its snapshot.
if [[ -d "$SOURCE/meetings" ]]; then
  while IFS= read -r -d '' source_path; do
    relative_path="${source_path#"$SOURCE/"}"
    destination_path="$DESTINATION/$relative_path"
    mkdir -p "$(dirname "$destination_path")"
    install -m 600 "$source_path" "$destination_path"
    updated=$((updated + 1))
  done < <(find "$SOURCE/meetings" -type f -name '*.jsonl' -print0)
fi

# Keep the human-readable, calendar-organised conversation archive alongside
# the SQLite index and compact memory cards.  These notes contain the exact
# completed turns for a local day, so preserve their directory structure and
# private permissions in the Git backup too.
if [[ -d "$SOURCE/daily" ]]; then
  while IFS= read -r -d '' source_path; do
    relative_path="${source_path#"$SOURCE/"}"
    destination_path="$DESTINATION/$relative_path"
    mkdir -p "$(dirname "$destination_path")"
    install -m 600 "$source_path" "$destination_path"
    updated=$((updated + 1))
  done < <(find "$SOURCE/daily" -type f -name '*.md' -print0)
fi

timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\n' "$timestamp" > "$DESTINATION/backup-updated-at.txt"
echo "Updated $updated private memory file(s) at $timestamp"

if [[ "$PUBLISH" == true ]]; then
  if [[ "$GIT_BACKUP" != true ]]; then
    echo "Private memory snapshot is current; no private Git repository is configured."
    exit 0
  fi
  git -C "$ROOT" add -- backups/jarvis-memory
  if git -C "$ROOT" diff --cached --quiet -- backups/jarvis-memory; then
    echo "Memory backup is already current."
    exit 0
  fi
  git -C "$ROOT" commit -m "Update MERRICK memory backup ($timestamp)"
  git -C "$ROOT" push
fi
