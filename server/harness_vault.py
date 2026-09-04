"""Persistent, fail-closed state boundary for MERRICK Harness Mode."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_VAULT_DIR = (
    Path.home() / "Library" / "Application Support" / "JarvisStark" / "PluginVault"
)
SCHEMA_VERSION = 1


class HarnessVaultError(RuntimeError):
    """Safe local vault initialization error."""


def _enabled() -> bool:
    return os.getenv("JARVIS_HARNESS_MODE_V1", "").strip().lower() == "true"


def _vault_dir() -> Path:
    configured = os.getenv("JARVIS_PLUGIN_VAULT_DIR", "").strip()
    return Path(configured) if configured else DEFAULT_VAULT_DIR


def _initialize(vault: Path) -> tuple[int, int]:
    if vault.is_symlink():
        raise HarnessVaultError("The Harness vault path is not a private directory.")
    vault.mkdir(parents=True, mode=0o700, exist_ok=True)
    vault.chmod(0o700)
    if not vault.is_dir() or vault.stat().st_uid != os.getuid():
        raise HarnessVaultError("The Harness vault is not owned by this macOS user.")

    database = vault / "registry.sqlite"
    if database.is_symlink() or (
        database.exists()
        and (not database.is_file() or database.stat().st_uid != os.getuid())
    ):
        raise HarnessVaultError("The Harness registry is not a private file.")
    with closing(sqlite3.connect(database, timeout=2.0)) as connection:
        with connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS schema_metadata (
                       singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                       version INTEGER NOT NULL,
                       updated_at TEXT NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS active_sets (
                       generation INTEGER PRIMARY KEY,
                       state TEXT NOT NULL CHECK (state IN ('active', 'superseded')),
                       user_plugin_count INTEGER NOT NULL CHECK (user_plugin_count >= 0),
                       created_at TEXT NOT NULL
                   )"""
            )
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT OR IGNORE INTO schema_metadata VALUES (1, ?, ?)",
                (SCHEMA_VERSION, now),
            )
            connection.execute(
                "INSERT OR IGNORE INTO active_sets VALUES (0, 'active', 0, ?)",
                (now,),
            )
            version = connection.execute(
                "SELECT version FROM schema_metadata WHERE singleton = 1"
            ).fetchone()
            active = connection.execute(
                "SELECT generation, user_plugin_count FROM active_sets WHERE state = 'active'"
            ).fetchone()
    database.chmod(0o600)
    if version is None or version[0] != SCHEMA_VERSION or active is None:
        raise HarnessVaultError("The Harness vault schema is incompatible.")
    return int(active[0]), int(active[1])


def snapshot() -> dict[str, Any]:
    """Return the bounded HUD projection without exposing a mutable path."""
    if not _enabled():
        return {
            "available": False,
            "status": "disabled",
            "schema_version": SCHEMA_VERSION,
            "active_generation": 0,
            "user_plugins": 0,
            "production_runtime": False,
        }
    generation, plugin_count = _initialize(_vault_dir())
    return {
        "available": True,
        "status": "ready",
        "schema_version": SCHEMA_VERSION,
        "active_generation": generation,
        "user_plugins": plugin_count,
        # M0 is deliberately inventory-only. A separate runtime flag will be
        # introduced only after sandbox, approval and rollback gates pass.
        "production_runtime": False,
    }


def safe_snapshot() -> dict[str, Any]:
    """Keep the capability inventory available when the optional vault fails."""
    try:
        return snapshot()
    except (HarnessVaultError, OSError, sqlite3.DatabaseError):
        return {
            "available": False,
            "status": "unavailable",
            "schema_version": SCHEMA_VERSION,
            "active_generation": 0,
            "user_plugins": 0,
            "production_runtime": False,
            "error_code": "VAULT_UNAVAILABLE",
        }
