"""Redacted capability status for the governed personal-operations surface.

This module deliberately exposes only an allowlisted, presentation-safe view.
Provider credentials and runtime configuration never cross the WebSocket.
"""

from __future__ import annotations

import os
from typing import Mapping, Optional


_CAPABILITIES = (
    {
        "id": "work",
        "status": "local_ready",
        "max_risk": "R1",
        "can_execute": True,
    },
    {
        "id": "mail",
        "status": "not_connected",
        "max_risk": "R2",
        "can_execute": False,
    },
    {
        "id": "calendar",
        "status": "not_connected",
        "max_risk": "R2",
        "can_execute": False,
    },
    {
        "id": "travel",
        "status": "handoff_only",
        "max_risk": "R3",
        "can_execute": False,
    },
)


def build_personal_operations_snapshot(
    *, environment: Optional[Mapping[str, str]] = None
) -> dict:
    """Return the public status contract for personal-operations capabilities.

    Only the exact value ``1`` enables the evolving V1 execution surface. The
    read-only status card remains visible while disabled so an unavailable
    connector cannot be mistaken for a working integration.
    """

    source = os.environ if environment is None else environment
    enabled = source.get("JARVIS_PERSONAL_OPERATIONS_V1") == "1"
    return {
        "schema_version": 1,
        "enabled": enabled,
        "mode": "guarded",
        "capabilities": [dict(capability) for capability in _CAPABILITIES],
        "policy": {
            "read": "automatic_when_connected",
            "external_write": "approval_required",
            "financial_legal": "user_handoff",
        },
    }
