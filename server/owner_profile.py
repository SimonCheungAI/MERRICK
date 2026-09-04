"""Per-device owner presentation preferences.

This module deliberately contains no memory, voiceprint, or model logic.  It
only turns the locally supplied language-specific forms of address into the
small trusted prompt fragment used for a verified speaker.
"""

from __future__ import annotations

import os


DEFAULT_ADDRESSES = {"en": "sir", "zh": "先生"}
_MAX_ADDRESS_CHARS = 32


def configured_owner_address(language: str) -> str:
    """Read the native host's per-device value with a safe local default."""
    normalized_language = "zh" if language == "zh" else "en"
    key = "JARVIS_OWNER_ADDRESS_ZH" if normalized_language == "zh" else "JARVIS_OWNER_ADDRESS_EN"
    fallback = DEFAULT_ADDRESSES[normalized_language]
    value = os.environ.get(key, fallback).strip()
    if not value or len(value) > _MAX_ADDRESS_CHARS:
        return fallback
    if any(character.isspace() and character != " " for character in value):
        return fallback
    return value


def identity_presentation_prompt(is_owner: bool, address: str = "sir") -> str:
    """Return model-only identity guidance; never expose verification details."""
    safe_address = address.strip()[:_MAX_ADDRESS_CHARS] or "sir"
    if is_owner:
        return (
            "\n<trusted_identity>The speaker for this turn is the verified owner. "
            f"Address them as '{safe_address}' naturally when an address is useful. Do not explain "
            "or mention speaker verification.</trusted_identity>"
        )
    return (
        "\n<trusted_identity>The speaker for this turn is an unverified guest. Never call "
        f"them '{safe_address}', never imply that you know them, and do not mention speaker verification. "
        "Use a neutral, natural form of address or no title.</trusted_identity>"
    )
