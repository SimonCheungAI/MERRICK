"""Local MCP bridge exposing MERRICK's bounded document library to Codex."""

from __future__ import annotations

import json
import os
from pathlib import Path

try:  # ``uvicorn --app-dir server`` and package imports use different roots.
    from library import LibraryError, ReadOnlyLibrary
except ModuleNotFoundError:  # pragma: no cover - exercised by package-level tests
    from server.library import LibraryError, ReadOnlyLibrary
from mcp.server.fastmcp import FastMCP


WORKSPACE_ROOT = Path(
    os.getenv(
        "JARVIS_WORKSPACE_DIR",
        Path.home() / "Library" / "Application Support" / "JarvisStark" / "Workspace" / "Documents",
    )
).expanduser()
library = ReadOnlyLibrary()
mcp = FastMCP(
    "jarvis-codex-bridge",
    instructions=(
        "Use the document tools only for the user's MERRICK workspace document folder. "
        "Never infer access to other local paths. The bridge returns only user documents "
        "and excludes MERRICK internal workspace files."
    ),
)


@mcp.tool()
def jarvis_workspace_status() -> str:
    """Return the only workspace MERRICK voice tasks may modify."""
    WORKSPACE_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    return json.dumps(
        {
            "workspace": str(WORKSPACE_ROOT),
            "policy": "Codex may read and write this workspace only; delete, move, and rename remain disabled for MERRICK voice tasks.",
        }
    )


@mcp.tool()
def jarvis_list_library_documents() -> str:
    """List readable user documents in MERRICK's unified workspace folder."""
    return json.dumps({"documents": library.list_documents()}, ensure_ascii=False)


@mcp.tool()
def jarvis_read_library_document(document_request: str, question: str = "") -> str:
    """Read one matching workspace document and return only ranked excerpts."""
    try:
        document = library.read_document(library.choose_document(document_request))
        context = library.relevant_context(document, question or document_request)
        return json.dumps(context, ensure_ascii=False)
    except LibraryError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
