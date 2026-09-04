import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server import codex_mcp
from server.library import ReadOnlyLibrary


class CodexMcpTests(unittest.TestCase):
    def test_library_tool_returns_bounded_document_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Merrick Library"
            root.mkdir()
            (root / "paper.md").write_text(
                "# Paper\n\nThe experiment uses a held-out test set.", encoding="utf-8"
            )
            with patch.object(codex_mcp, "library", ReadOnlyLibrary(root=root, cache_root=Path(temporary) / "cache")):
                response = json.loads(codex_mcp.jarvis_read_library_document("read paper", "experiment"))
        self.assertEqual(response["kind"], "local_document")
        self.assertIn("held-out", response["text"])

    def test_workspace_status_names_a_single_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(codex_mcp, "WORKSPACE_ROOT", Path(temporary) / "workspace"):
                response = json.loads(codex_mcp.jarvis_workspace_status())
        self.assertEqual(response["policy"].split(";", 1)[0], "Codex may read and write this workspace only")


if __name__ == "__main__":
    unittest.main()
