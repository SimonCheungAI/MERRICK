"""Local, low-latency durable memory for MERRICK

The store deliberately uses only Python's standard library and SQLite FTS5.
Its compact hashed vectors are a private local retrieval index: no transcript
or embedding request leaves the Mac.  The design leaves a clean replacement
point for a future downloaded local semantic encoder without changing the
database schema or the voice-path API.
"""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
import threading
from array import array
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


VECTOR_DIMENSIONS = 384
MAX_EPISODE_CHARS = 6_000
CONTINUITY_MIN_SCORE = 0.34
PREFERENCE_PROPOSAL_EVIDENCE = 3
PREFERENCE_KEY_RE = re.compile(r"preference(?:\.[a-z0-9_-]+)+", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9]{2,}|[\u4e00-\u9fff]", re.IGNORECASE)
FTS_QUERY_TOKEN_RE = re.compile(r"[a-z0-9]{2,}|[\u4e00-\u9fff]+", re.IGNORECASE)
FTS_STOP_WORDS = frozenset({
    "about", "again", "and", "are", "can", "could", "did", "discuss",
    "discussion", "do", "earlier", "for", "from", "have", "how", "i",
    "is", "it", "last", "me", "my", "of", "our", "please", "previous",
    "remember", "said", "that", "the", "this", "to", "us", "was", "we",
    "what", "when", "with", "would", "you", "your",
})
CJK_CONTINUITY_NOISE_RE = re.compile(
    r"我们|咱们|这个|那个|这些|那些|继续|接着|再聊|回到|说回|关于|"
    r"提到|跟进|后续|下一步|进展|后来|现在|怎么样了?|如何了?|到哪一步了?|"
    r"有什么进展|项目|计划|方案|报告|事情"
)
SIGNIFICANT_TURN_RE = re.compile(
    r"\b(?:we\s+(?:decided|should|will)|let'?s\s+|i(?:'m|\s+am)\s+going\s+to|"
    r"i\s+(?:will|need\s+to)|(?:project|paper|deadline|plan|decision|important))\b",
    re.IGNORECASE,
)
PREFERENCE_TENDENCY_RE = re.compile(
    r"\b(?:i\s+(?:like|love|prefer|enjoy|dislike|hate|don't\s+like)|"
    r"my\s+favo(?:u)?rite\s+is|i(?:'m|\s+am)\s+into)\b",
    re.IGNORECASE,
)


# Completed turns may be consolidated from short-lived background workers.
# Serialise the human-readable daily archive so two completed replies can never
# interleave their Markdown blocks.
_DAILY_ARCHIVE_LOCK = threading.Lock()


@dataclass(frozen=True)
class MemoryHit:
    user_text: str
    assistant_text: str
    created_at: str
    score: float


class LocalMemoryStore:
    """SQLite/FTS plus a local exact vector index for personal-scale history."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / "jarvis-memory.db"

    def _connect(self) -> sqlite3.Connection:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5.0)
        # SQLite creates its file using the process umask. Tighten it
        # explicitly because this database contains private conversations.
        self.path.chmod(0o600)
        connection.row_factory = sqlite3.Row
        # A single-file journal keeps the private Git snapshot consistent on
        # exit; the memory workload is tiny and all work happens off the voice
        # response path.
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY,
                source_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                user_text TEXT NOT NULL,
                assistant_text TEXT NOT NULL,
                importance REAL NOT NULL DEFAULT 0.2,
                consolidated_at TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                episode_id UNINDEXED,
                content,
                tokenize='unicode61'
            );
            CREATE TABLE IF NOT EXISTS episode_vectors (
                episode_id INTEGER PRIMARY KEY REFERENCES episodes(id) ON DELETE CASCADE,
                dimensions INTEGER NOT NULL,
                vector BLOB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY,
                episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'candidate'
            );
            CREATE INDEX IF NOT EXISTS observations_episode_idx ON observations(episode_id);
            CREATE INDEX IF NOT EXISTS observations_status_idx ON observations(status, created_at);
            CREATE TABLE IF NOT EXISTS preference_lifecycle (
                id INTEGER PRIMARY KEY,
                preference_key TEXT NOT NULL,
                value_hash TEXT NOT NULL,
                value TEXT NOT NULL,
                stage TEXT NOT NULL CHECK(stage IN ('candidate', 'proposed', 'active', 'superseded')),
                confidence REAL NOT NULL,
                evidence_count INTEGER NOT NULL DEFAULT 1,
                first_observed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source_episode_id INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
                active_revision_id TEXT,
                UNIQUE(preference_key, value_hash)
            );
            CREATE INDEX IF NOT EXISTS preference_lifecycle_key_stage_idx
                ON preference_lifecycle(preference_key, stage, updated_at DESC);
            CREATE INDEX IF NOT EXISTS preference_lifecycle_stage_idx
                ON preference_lifecycle(stage, updated_at DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS preference_lifecycle_one_active_idx
                ON preference_lifecycle(preference_key) WHERE stage = 'active';
            """
        )
        return connection

    @staticmethod
    def _normalise(value: str, limit: int) -> str:
        return re.sub(r"\s+", " ", value).strip()[:limit]

    @classmethod
    def _features(cls, text: str) -> list[str]:
        normalized = cls._normalise(text.casefold(), MAX_EPISODE_CHARS)
        words = TOKEN_RE.findall(normalized)
        # Character n-grams make local retrieval tolerant of small ASR and
        # inflection differences without requiring a downloaded model.
        compact = re.sub(r"\s+", " ", normalized)
        grams = [compact[index:index + 3] for index in range(max(0, len(compact) - 2))]
        return words + [f"g:{gram}" for gram in grams if gram.strip()]

    @classmethod
    def _vector(cls, text: str) -> array:
        values = array("f", [0.0]) * VECTOR_DIMENSIONS
        for feature in cls._features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % VECTOR_DIMENSIONS
            direction = 1.0 if digest[4] & 1 else -1.0
            values[bucket] += direction
        norm = math.sqrt(sum(value * value for value in values))
        if norm:
            for index, value in enumerate(values):
                values[index] = value / norm
        return values

    @staticmethod
    def _cosine(left: array, right: array) -> float:
        if len(left) != len(right):
            return 0.0
        return sum(a * b for a, b in zip(left, right))

    @staticmethod
    def _source_key(user_text: str, assistant_text: str) -> str:
        payload = f"{user_text}\n{assistant_text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def _importance(cls, user_text: str) -> float:
        return 0.85 if SIGNIFICANT_TURN_RE.search(user_text) else 0.2

    @classmethod
    def _fts_query(cls, text: str) -> str:
        # Exclude conversational scaffolding such as "do you remember". It
        # otherwise matches nearly every episode and can bury the actual topic
        # (for example "Marvel") under unrelated recent memories.
        tokens = [
            token for token in FTS_QUERY_TOKEN_RE.findall(text.casefold())
            if token not in FTS_STOP_WORDS and len(token) >= 2
        ]
        return " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens[:12])

    @classmethod
    def _cjk_topic_bigrams(cls, text: str) -> set[str]:
        """Return small Chinese topic anchors after removing follow-up phrasing."""
        topical = CJK_CONTINUITY_NOISE_RE.sub("", cls._normalise(text, 1_000))
        compact = "".join(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", topical))
        if len(compact) < 3:
            return set()
        return {compact[index:index + 2] for index in range(len(compact) - 1)}

    def record_episode(self, user_text: str, assistant_text: str) -> int | None:
        user = self._normalise(user_text, MAX_EPISODE_CHARS)
        answer = self._normalise(assistant_text, MAX_EPISODE_CHARS)
        if not user or not answer:
            return None
        source_key = self._source_key(user, answer)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        combined = f"User: {user}\nMERRICK: {answer}"
        connection = self._connect()
        try:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO episodes
                        (source_key, created_at, user_text, assistant_text, importance)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (source_key, timestamp, user, answer, self._importance(user)),
                )
                if cursor.rowcount == 0:
                    row = connection.execute(
                        "SELECT id FROM episodes WHERE source_key = ?", (source_key,)
                    ).fetchone()
                    return int(row["id"]) if row else None
                episode_id = int(cursor.lastrowid)
                connection.execute(
                    "INSERT INTO episodes_fts (episode_id, content) VALUES (?, ?)",
                    (episode_id, combined),
                )
                connection.execute(
                    "INSERT INTO episode_vectors (episode_id, dimensions, vector) VALUES (?, ?, ?)",
                    (episode_id, VECTOR_DIMENSIONS, self._vector(combined).tobytes()),
                )
                return episode_id
        finally:
            connection.close()

    def append_daily_turn(
        self,
        user_text: str,
        assistant_text: str,
        *,
        when: datetime | None = None,
    ) -> Path | None:
        """Append one owner conversation turn to its local-calendar-day note.

        SQLite remains the retrieval authority.  These Markdown notes are a
        precise, user-browsable daily record: each block keeps the local date
        and time along with the complete normalised exchange.
        """
        user = self._normalise(user_text, MAX_EPISODE_CHARS)
        answer = self._normalise(assistant_text, MAX_EPISODE_CHARS)
        if not user or not answer:
            return None
        local_time = (when or datetime.now().astimezone()).astimezone()
        directory = self.directory / "daily"
        path = directory / f"{local_time.strftime('%Y-%m-%d')}.md"
        block = (
            f"\n## {local_time.strftime('%H:%M')} {local_time.tzname() or ''}\n\n"
            f"**You:** {user}\n\n"
            f"**MERRICK:** {answer}\n"
        )
        with _DAILY_ARCHIVE_LOCK:
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            is_new = not path.exists()
            with path.open("a", encoding="utf-8") as handle:
                if is_new:
                    handle.write(f"# MERRICK conversation — {local_time.strftime('%Y-%m-%d')}\n")
                handle.write(block)
            path.chmod(0o600)
        return path

    def consolidate_episode(self, episode_id: int) -> None:
        """Extract only a conservative, reviewable observation in the background."""
        connection = self._connect()
        try:
            with connection:
                row = connection.execute(
                    "SELECT user_text, importance, consolidated_at FROM episodes WHERE id = ?",
                    (episode_id,),
                ).fetchone()
                if row is None or row["consolidated_at"]:
                    return
                now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                if row["importance"] >= 0.8:
                    # This is deliberately an observation, not a permanent
                    # preference. Explicit "remember" / "forget" commands remain
                    # the only path to durable fact cards in the active prompt.
                    connection.execute(
                        """
                        INSERT INTO observations (episode_id, created_at, kind, value, confidence, status)
                        VALUES (?, ?, 'possible_decision', ?, 0.68, 'candidate')
                        """,
                        (episode_id, now, self._normalise(str(row["user_text"]), 600)),
                    )
                if PREFERENCE_TENDENCY_RE.search(str(row["user_text"])):
                    # This is deliberately not an active preference. It gives
                    # the background consolidator local evidence to organise
                    # later, without making an incidental remark control the
                    # assistant's personality or replies.
                    connection.execute(
                        """
                        INSERT INTO observations (episode_id, created_at, kind, value, confidence, status)
                        VALUES (?, ?, 'preference_candidate', ?, 0.55, 'candidate')
                        """,
                        (episode_id, now, self._normalise(str(row["user_text"]), 600)),
                    )
                connection.execute(
                    "UPDATE episodes SET consolidated_at = ? WHERE id = ?", (now, episode_id)
                )
        finally:
            connection.close()

    def bootstrap_legacy(self, records: Iterable[tuple[str, str]]) -> None:
        """One-way local import of the previous JSONL archive, deduplicated by hash."""
        for user_text, assistant_text in records:
            episode_id = self.record_episode(user_text, assistant_text)
            if episode_id is not None:
                self.consolidate_episode(episode_id)

    def preference_candidates(self, *, limit: int = 6) -> list[str]:
        """Return local, unconfirmed preference observations for later consolidation."""
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT value FROM observations
                WHERE kind = 'preference_candidate' AND status = 'candidate'
                ORDER BY id DESC LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
            return [str(row["value"]) for row in rows if str(row["value"]).strip()]
        finally:
            connection.close()

    @classmethod
    def _preference_identity(cls, preference_key: str, value: str) -> tuple[str, str, str]:
        key = cls._normalise(preference_key.casefold(), 96)
        normalized_value = cls._normalise(value, 600)
        if not PREFERENCE_KEY_RE.fullmatch(key) or not normalized_value:
            return ("", "", "")
        value_hash = hashlib.sha256(normalized_value.casefold().encode("utf-8")).hexdigest()
        return (key, normalized_value, value_hash)

    def record_preference_candidate(
        self,
        preference_key: str,
        value: str,
        *,
        source_episode_id: int | None = None,
        confidence: float = 0.55,
    ) -> str:
        """Accumulate evidence locally without silently activating a preference."""
        key, normalized_value, value_hash = self._preference_identity(preference_key, value)
        if not key:
            return ""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        bounded_confidence = min(0.99, max(0.0, float(confidence)))
        connection = self._connect()
        try:
            with connection:
                row = connection.execute(
                    """SELECT id, stage, confidence, evidence_count
                       FROM preference_lifecycle
                       WHERE preference_key=? AND value_hash=?""",
                    (key, value_hash),
                ).fetchone()
                if row is None:
                    connection.execute(
                        """INSERT INTO preference_lifecycle
                           (preference_key, value_hash, value, stage, confidence,
                            evidence_count, first_observed_at, updated_at, source_episode_id)
                           VALUES (?, ?, ?, 'candidate', ?, 1, ?, ?, ?)""",
                        (key, value_hash, normalized_value, bounded_confidence, now, now, source_episode_id),
                    )
                    return "candidate"
                stage = str(row["stage"])
                if stage in {"active", "superseded"}:
                    return stage
                evidence_count = int(row["evidence_count"]) + 1
                stage = "proposed" if evidence_count >= PREFERENCE_PROPOSAL_EVIDENCE else "candidate"
                connection.execute(
                    """UPDATE preference_lifecycle
                       SET stage=?, confidence=?, evidence_count=?, updated_at=?,
                           source_episode_id=COALESCE(?, source_episode_id)
                       WHERE id=?""",
                    (
                        stage,
                        min(0.95, max(float(row["confidence"]), bounded_confidence) + 0.08),
                        evidence_count,
                        now,
                        source_episode_id,
                        int(row["id"]),
                    ),
                )
                return stage
        finally:
            connection.close()

    def preference_lifecycle(self, preference_key: str) -> list[dict[str, object]]:
        """Return one key's lifecycle for owner-authorized review and tests."""
        key = self._normalise(preference_key.casefold(), 96)
        if not PREFERENCE_KEY_RE.fullmatch(key):
            return []
        connection = self._connect()
        try:
            rows = connection.execute(
                """SELECT value, stage, confidence, evidence_count, updated_at,
                          active_revision_id
                   FROM preference_lifecycle WHERE preference_key=?
                   ORDER BY updated_at DESC, id DESC""",
                (key,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def activate_preference(
        self,
        preference_key: str,
        value: str,
        *,
        revision_id: str,
        confidence: float = 1.0,
    ) -> None:
        """Make one confirmed value active and retire every older value for its key."""
        key, normalized_value, value_hash = self._preference_identity(preference_key, value)
        revision = self._normalise(revision_id, 48)
        if not key or not revision:
            return
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        bounded_confidence = min(1.0, max(0.0, float(confidence)))
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """UPDATE preference_lifecycle
                       SET stage='superseded', updated_at=?
                       WHERE preference_key=? AND value_hash<>? AND stage<>'superseded'""",
                    (now, key, value_hash),
                )
                row = connection.execute(
                    """SELECT id FROM preference_lifecycle
                       WHERE preference_key=? AND value_hash=?""",
                    (key, value_hash),
                ).fetchone()
                if row is None:
                    connection.execute(
                        """INSERT INTO preference_lifecycle
                           (preference_key, value_hash, value, stage, confidence,
                            evidence_count, first_observed_at, updated_at, active_revision_id)
                           VALUES (?, ?, ?, 'active', ?, 1, ?, ?, ?)""",
                        (key, value_hash, normalized_value, bounded_confidence, now, now, revision),
                    )
                else:
                    connection.execute(
                        """UPDATE preference_lifecycle
                           SET stage='active', confidence=?, updated_at=?, active_revision_id=?
                           WHERE id=?""",
                        (bounded_confidence, now, revision, int(row["id"])),
                    )
        finally:
            connection.close()

    def forget_preference(self, preference_key: str) -> None:
        """Remove one preference's lifecycle so old evidence cannot resurrect it."""
        key = self._normalise(preference_key.casefold(), 96)
        if not PREFERENCE_KEY_RE.fullmatch(key):
            return
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    "DELETE FROM preference_lifecycle WHERE preference_key=?",
                    (key,),
                )
        finally:
            connection.close()

    def search(self, query: str, *, limit: int = 3) -> list[MemoryHit]:
        phrase = self._normalise(query, 1_000)
        if not phrase:
            return []
        query_vector = self._vector(phrase)
        connection = self._connect()
        try:
            lexical: dict[int, float] = {}
            fts_query = self._fts_query(phrase)
            if fts_query:
                try:
                    rows = connection.execute(
                        """
                        SELECT episode_id, bm25(episodes_fts) AS rank
                        FROM episodes_fts WHERE episodes_fts MATCH ?
                        ORDER BY rank LIMIT ?
                        """,
                        (fts_query, max(limit * 6, 18)),
                    ).fetchall()
                    for position, row in enumerate(rows):
                        lexical[int(row["episode_id"])] = 1.0 / (position + 1)
                except sqlite3.OperationalError:
                    pass
            candidates = connection.execute(
                """
                SELECT episodes.id, episodes.created_at, episodes.user_text, episodes.assistant_text,
                       episodes.importance, episode_vectors.vector
                FROM episodes JOIN episode_vectors ON episode_vectors.episode_id = episodes.id
                ORDER BY episodes.id DESC LIMIT 2_000
                """
            ).fetchall()
        finally:
            connection.close()
        scored: list[MemoryHit] = []
        for row in candidates:
            raw = row["vector"]
            vector = array("f")
            vector.frombytes(raw)
            semantic = max(0.0, self._cosine(query_vector, vector))
            lexical_score = lexical.get(int(row["id"]), 0.0)
            # If FTS found an exact topical anchor, do not let a weak hashed
            # vector collision add unrelated history. When FTS finds nothing,
            # vector retrieval remains available for paraphrased recall.
            if lexical and not lexical_score:
                continue
            # Exact private-vector retrieval and FTS complement one another;
            # a small importance term helps recover decisions without making
            # them part of every prompt.
            score = semantic * 0.56 + lexical_score * 0.38 + float(row["importance"]) * 0.06
            if score > 0.04:
                scored.append(MemoryHit(
                    user_text=str(row["user_text"]),
                    assistant_text=str(row["assistant_text"]),
                    created_at=str(row["created_at"]),
                    score=score,
                ))
        return sorted(scored, key=lambda hit: (hit.score, hit.created_at), reverse=True)[:limit]

    def search_continuity(
        self,
        query: str,
        *,
        limit: int = 2,
        exclude_turns: Iterable[tuple[str, str]] = (),
    ) -> list[MemoryHit]:
        """Retrieve a confident older episode for natural topic continuation."""
        excluded = {
            (
                self._normalise(user_text, MAX_EPISODE_CHARS),
                self._normalise(assistant_text, MAX_EPISODE_CHARS),
            )
            for user_text, assistant_text in exclude_turns
        }
        candidates = self.search(query, limit=max(limit * 4, 8))
        query_cjk_topics = self._cjk_topic_bigrams(query)
        return [
            hit
            for hit in candidates
            if (
                hit.score >= CONTINUITY_MIN_SCORE
                or len(
                    query_cjk_topics
                    & self._cjk_topic_bigrams(f"{hit.user_text} {hit.assistant_text}")
                ) >= 2
            )
            and (hit.user_text, hit.assistant_text) not in excluded
        ][:max(1, limit)]
