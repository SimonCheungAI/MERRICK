"""Local, bounded change audit for a user-authorized MERRICK workspace."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MAX_TRACKED_FILES = 10_000
MAX_SNAPSHOT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class _FileState:
    digest: str
    size: int
    snapshot: Path | None


class WorkspaceMutationAudit:
    """Capture change metadata and bounded pre-images around one file turn.

    The model's existing workspace tools may alter several files in one turn.
    This observer creates pre-images before that turn begins, then appends one
    metadata-only JSONL record per changed path after it ends. It never stores
    the spoken request itself, credentials, or an unrestricted path.
    """

    def __init__(self, root: Path, *, state_root: Path | None = None) -> None:
        self.root = root.expanduser().resolve()
        self.state_root = (state_root or (
            Path.home() / "Library" / "Application Support" / "JarvisStark" / "FileAudit"
        )).expanduser().resolve()
        self._before: dict[str, _FileState] = {}
        self._turn_id = ""
        self._request_digest = ""

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(256 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def _snapshot(self, stage: str) -> dict[str, _FileState]:
        states: dict[str, _FileState] = {}
        if not self.root.is_dir():
            return states
        for candidate in self.root.rglob("*"):
            if len(states) >= MAX_TRACKED_FILES:
                break
            try:
                resolved = candidate.resolve(strict=True)
                if self.root not in resolved.parents or not resolved.is_file():
                    continue
                relative = resolved.relative_to(self.root).as_posix()
                size = resolved.stat().st_size
                digest = self._sha256(resolved)
            except OSError:
                continue
            retained: Path | None = None
            if stage == "before" and size <= MAX_SNAPSHOT_BYTES:
                retained = self.state_root / "revisions" / self._turn_id / relative
                try:
                    retained.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(resolved, retained)
                    os.chmod(retained, 0o600)
                except OSError:
                    retained = None
            states[relative] = _FileState(digest=digest, size=size, snapshot=retained)
        return states

    def begin(self, *, turn_id: str, request_text: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.state_root, 0o700)
        self._turn_id = turn_id or uuid.uuid4().hex
        self._request_digest = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
        self._before = self._snapshot("before")

    def finish(self) -> list[dict[str, object]]:
        if not self._turn_id:
            return []
        after = self._snapshot("after")
        records: list[dict[str, object]] = []
        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        for relative in sorted(set(self._before) | set(after)):
            before, current = self._before.get(relative), after.get(relative)
            if before and current and before.digest == current.digest:
                continue
            operation = "create" if before is None else "quarantine_delete" if current is None else "update"
            record = {
                "id": uuid.uuid4().hex,
                "completed_at": now,
                "turn_id": self._turn_id[:128],
                "request_digest": self._request_digest,
                "operation": operation,
                "path": relative,
                "before_hash": before.digest if before else "",
                "after_hash": current.digest if current else "",
                "before_bytes": before.size if before else 0,
                "after_bytes": current.size if current else 0,
                "before_snapshot": str(before.snapshot.relative_to(self.state_root)) if before and before.snapshot else "",
                "reversible": bool(before and before.snapshot),
            }
            records.append(record)
        if records:
            log_path = self.state_root / "operations.jsonl"
            with log_path.open("a", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            os.chmod(log_path, 0o600)
        return records
