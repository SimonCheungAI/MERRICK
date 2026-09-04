"""Static contracts for the Agent Board presentation boundary."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MultiAgentUIContractTests(unittest.TestCase):
    def test_board_has_live_controls_and_is_wired_to_socket_messages(self) -> None:
        markup = (PROJECT_ROOT / "web/index.html").read_text(encoding="utf-8")
        app = (PROJECT_ROOT / "web/app.js").read_text(encoding="utf-8")
        board = (PROJECT_ROOT / "web/agent-board.js").read_text(encoding="utf-8")

        for required_id in (
            'id="agent-board-btn"', 'id="agent-board-panel"',
            'id="agent-board-content"', 'id="agent-board-cancel-btn"',
            'id="agent-board-new-btn"', 'id="agent-board-create-form"',
            'id="agent-board-name-input"', 'id="agent-board-task-input"',
        ):
            self.assertIn(required_id, markup)
        self.assertIn('case "multi_agent_state"', app)
        self.assertIn('"merrick-agent-board-send"', app)
        self.assertIn("__merrickPendingMultiAgentMessage", app)
        self.assertIn("__merrickPendingMultiAgentMessage", board)
        self.assertIn('type: "multi_agent_cancel"', board)
        self.assertIn('type: "multi_agent_spawn"', board)
        self.assertIn('type: "multi_agent_close_child"', board)
        self.assertIn('nativePost("openOpenClawSession", { url })', board)
        self.assertIn('child.can_open !== true', board)
        self.assertGreaterEqual(board.count('type: "multi_agent_refresh"'), 3)

    def test_board_uses_safe_text_nodes_and_scrolls_inside_narrow_windows(self) -> None:
        board = (PROJECT_ROOT / "web/agent-board.js").read_text(encoding="utf-8")
        styles = (PROJECT_ROOT / "web/style.css").read_text(encoding="utf-8")

        self.assertNotIn("innerHTML", board)
        self.assertIn("textContent", board)
        self.assertIn("overflow-y: auto", styles)
        self.assertIn("width: min(430px, calc(100vw - 32px))", styles)
        self.assertIn("max-height: inherit", styles)
        self.assertIn("minmax(0, 1fr)", styles)
        self.assertIn("agent-card-terminal", styles)
        self.assertIn("agent-card-close", styles)
        self.assertIn("agent-board-create-form", styles)


if __name__ == "__main__":
    unittest.main()
