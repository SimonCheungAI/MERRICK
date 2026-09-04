from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

import main as merrick_main  # noqa: E402
from organizer import OrganizerStore  # noqa: E402


class OpenClawOrganizerBridgeTests(unittest.TestCase):
    def test_tool_side_mutation_refreshes_connected_organizer_sessions(self) -> None:
        class FakeSession:
            def __init__(self) -> None:
                self.snapshot_requests = 0

            async def send_organizer_snapshot(self) -> None:
                self.snapshot_requests += 1

        session = FakeSession()
        merrick_main.active_organizer_sessions.add(session)
        try:
            import asyncio

            asyncio.run(merrick_main.publish_organizer_snapshot())
        finally:
            merrick_main.active_organizer_sessions.discard(session)
        self.assertEqual(session.snapshot_requests, 1)

    def test_create_list_and_complete_share_the_organizer_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = OrganizerStore(Path(directory))
            store.initialise()
            with patch.object(merrick_main, "_organizer_store", return_value=store):
                created = merrick_main.organizer_plugin_task_response(
                    {
                        "action": "create",
                        "items": [
                            {
                                "title": "Prepare the research brief",
                                "projectTitle": "MERRICK",
                                "dueAt": "2026-09-04T09:00:00+01:00",
                            }
                        ],
                    }
                )
                self.assertTrue(created["ok"])
                self.assertEqual(created["localState"], "committed")
                self.assertEqual(created["automationState"], "not_requested")
                task = created["tasks"][0]
                self.assertEqual(task["title"], "Prepare the research brief")
                self.assertEqual(task["project_title"], "MERRICK")

                listed = merrick_main.organizer_plugin_task_response({"action": "list"})
                self.assertEqual([item["id"] for item in listed["tasks"]], [task["id"]])

                completed = merrick_main.organizer_plugin_task_response(
                    {"action": "complete", "taskId": task["id"]}
                )
                self.assertEqual(completed["task"]["status"], "completed")
                self.assertEqual(store.snapshot()["tasks"][0]["status"], "completed")

    def test_openclaw_can_update_shared_task_and_reminder_times(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = OrganizerStore(Path(directory))
            store.initialise()
            task = store.create_task("Draft the brief")
            reminder = store.create_reminder(
                "Review the brief", "2026-09-04T09:00:00+01:00", task_id=task["id"]
            )
            with patch.object(merrick_main, "_organizer_store", return_value=store):
                updated_task = merrick_main.organizer_plugin_task_response(
                    {
                        "action": "update_task",
                        "taskId": task["id"],
                        "title": "Draft and review the brief",
                        "dueAt": "2026-09-04T10:00:00+01:00",
                    }
                )
                self.assertEqual(updated_task["task"]["title"], "Draft and review the brief")
                updated_reminder = merrick_main.organizer_plugin_task_response(
                    {
                        "action": "update_reminder",
                        "reminderId": reminder["id"],
                        "fireAt": "2026-09-04T11:00:00+01:00",
                    }
                )
                self.assertEqual(updated_reminder["reminder"]["fire_at"], "2026-09-04T11:00:00+01:00")

    def test_rejects_invalid_task_bridge_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = OrganizerStore(Path(directory))
            store.initialise()
            with patch.object(merrick_main, "_organizer_store", return_value=store):
                with self.assertRaisesRegex(ValueError, "between one and 24"):
                    merrick_main.organizer_plugin_task_response({"action": "create", "items": []})
                with self.assertRaisesRegex(ValueError, "Unsupported"):
                    merrick_main.organizer_plugin_task_response({"action": "schedule"})
                with self.assertRaisesRegex(LookupError, "no longer exists"):
                    merrick_main.organizer_plugin_task_response(
                        {"action": "complete", "taskId": "task-missing"}
                    )
