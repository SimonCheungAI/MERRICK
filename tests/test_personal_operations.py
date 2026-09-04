from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from personal_operations import build_personal_operations_snapshot  # noqa: E402


class PersonalOperationsSnapshotTests(unittest.TestCase):
    def test_external_operations_are_guarded_and_disconnected_by_default(self) -> None:
        snapshot = build_personal_operations_snapshot(environment={})

        self.assertEqual(snapshot["schema_version"], 1)
        self.assertFalse(snapshot["enabled"])
        self.assertEqual(snapshot["mode"], "guarded")
        self.assertEqual(snapshot["policy"]["external_write"], "approval_required")
        self.assertEqual(snapshot["policy"]["financial_legal"], "user_handoff")

        capabilities = {item["id"]: item for item in snapshot["capabilities"]}
        self.assertEqual(capabilities["work"]["status"], "local_ready")
        self.assertEqual(capabilities["mail"]["status"], "not_connected")
        self.assertEqual(capabilities["calendar"]["status"], "not_connected")
        self.assertEqual(capabilities["travel"]["status"], "handoff_only")
        self.assertFalse(capabilities["mail"]["can_execute"])
        self.assertFalse(capabilities["calendar"]["can_execute"])
        self.assertFalse(capabilities["travel"]["can_execute"])

    def test_feature_flag_accepts_only_an_explicit_true_value(self) -> None:
        self.assertTrue(
            build_personal_operations_snapshot(
                environment={"JARVIS_PERSONAL_OPERATIONS_V1": "1"}
            )["enabled"]
        )
        for value in ("", "0", "true", "yes", "enabled", "unexpected"):
            with self.subTest(value=value):
                self.assertFalse(
                    build_personal_operations_snapshot(
                        environment={"JARVIS_PERSONAL_OPERATIONS_V1": value}
                    )["enabled"]
                )

    def test_snapshot_uses_an_allowlist_and_never_exposes_secret_fields(self) -> None:
        snapshot = build_personal_operations_snapshot(
            environment={
                "JARVIS_PERSONAL_OPERATIONS_V1": "1",
                "GMAIL_ACCESS_TOKEN": "do-not-leak",
                "OPENCLAW_GATEWAY_TOKEN": "do-not-leak-either",
                "PASSWORD": "also-secret",
            }
        )
        rendered = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn("do-not-leak", rendered)

        forbidden_keys = {
            "access_token",
            "refresh_token",
            "password",
            "secret",
            "secret_ref",
            "api_key",
            "authorization",
        }

        def walk(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for nested in value.values():
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)

        walk(snapshot)


class PersonalOperationsDashboardWiringTests(unittest.TestCase):
    def test_existing_authenticated_organizer_snapshot_carries_operations_status(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn(
            'snapshot["personal_operations"] = build_personal_operations_snapshot()',
            backend,
        )
        self.assertIn('id="personal-operations-status"', html)
        self.assertIn("renderPersonalOperations(organizerSnapshot)", frontend)
        self.assertIn("snapshot?.personal_operations", frontend)
        self.assertIn('organizer_operations: "OPERATIONS CONTROL"', frontend)
        self.assertIn('organizer_operations: "操作控制"', frontend)

    def test_local_dashboard_snapshot_does_not_wait_for_openclaw_startup(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        run_start = backend.index("    async def run(self, *, subprotocol: str | None = None):")
        run_end = backend.index("\n\n@asynccontextmanager", run_start)
        session_run = backend[run_start:run_end]

        self.assertLess(
            session_run.index("await self.send_organizer_snapshot()"),
            session_run.index("self.prewarm_openclaw_runtime()"),
        )

    def test_desktop_ready_event_does_not_wait_for_openclaw_prewarm(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        run_start = backend.index("    async def run(self, *, subprotocol: str | None = None):")
        run_end = backend.index("\n\n@asynccontextmanager", run_start)
        session_run = backend[run_start:run_end]

        self.assertLess(
            session_run.index('await self.send({"type": "ready"})'),
            session_run.index("self.prewarm_openclaw_runtime()"),
        )

    def test_openclaw_prewarm_failure_keeps_the_local_dashboard_session_ready(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        prewarm_start = backend.index("    async def prewarm_openclaw_runtime(self):")
        prewarm_end = backend.index("\n    async def run(", prewarm_start)
        prewarm = backend[prewarm_start:prewarm_end]

        self.assertIn("await openclaw_gateway.prewarm()", prewarm)
        self.assertIn("self.use_openclaw = False", prewarm)
        self.assertIn("local work hub remains online", prewarm)
        self.assertNotIn("await self.ws.close()", prewarm)

    def test_websocket_disconnect_does_not_cancel_the_shared_gateway_prewarm(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        run_start = backend.index("    async def run(self, *, subprotocol: str | None = None):")
        run_end = backend.index("\n\n@asynccontextmanager", run_start)
        session_run = backend[run_start:run_end]

        self.assertNotIn("self.openclaw_prewarm_task.cancel()", session_run)

    def test_opening_a_cached_dashboard_does_not_leave_a_false_refresh_status(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        handler_start = frontend.index('organizerBtn?.addEventListener("click"')
        handler_end = frontend.index("organizerCloseBtn?.addEventListener", handler_start)
        open_handler = frontend[handler_start:handler_end]

        self.assertIn('setOrganizerVisible(true, "overview")', open_handler)
        self.assertNotIn("refreshRequested", open_handler)
        self.assertNotIn("organizer_snapshot_request", open_handler)

    def test_gateway_reconnects_back_off_until_a_real_ready_event(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function nextReconnectDelay()", frontend)
        self.assertIn("Math.min(30000, 3000 * (2 ** reconnectAttempts))", frontend)
        self.assertIn("reconnectAttempts = Math.min(reconnectAttempts + 1, 4)", frontend)
        ready_start = frontend.index('case "ready":')
        ready_end = frontend.index("break;", ready_start)
        self.assertIn("reconnectAttempts = 0", frontend[ready_start:ready_end])
        self.assertNotIn("setTimeout(connect, 3000)", frontend)


if __name__ == "__main__":
    unittest.main()
