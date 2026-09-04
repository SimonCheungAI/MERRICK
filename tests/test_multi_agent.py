"""Multi-agent orchestration tests with a deterministic Gateway double."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from multi_agent import MultiAgentRunController  # noqa: E402


class _FakeGateway:
    def __init__(self) -> None:
        self.spawned: list[dict] = []
        self.cancelled: list[str] = []
        self.wait_count = 0
        self.task_status = "succeeded"
        self.archived: list[dict] = []

    async def ensure_session(self, *, session_key, agent_id="main", label="MERRICK Agent Board"):
        return {"key": session_key, "label": label}

    async def invoke_rpc_tool(self, tool, args, *, session_key, agent_id="main", timeout=30.0):
        if tool == "sessions_spawn":
            self.spawned.append(args)
            index = len(self.spawned)
            return {
                "status": "accepted",
                "runId": f"run-{index}",
                "childSessionKey": f"agent:main:subagent-{index}",
                "sessionUrl": f"http://127.0.0.1:18789/#/sessions/subagent-{index}",
            }
        if tool == "sessions_list":
            archived = args.get("archived") is True
            keys = {item["sessionKey"] for item in self.archived}
            return {"sessions": [
                {
                    "key": f"agent:main:subagent-{index}",
                    "sessionId": f"session-{index}",
                    "archived": archived,
                }
                for index in range(1, len(self.spawned) + 1)
                if (f"agent:main:subagent-{index}" in keys) is archived
            ]}
        if tool == "sessions":
            self.archived.append(args)
            return {"status": "updated", "sessionKey": args["sessionKey"]}
        if tool == "sessions_history":
            return {"messages": [{
                "role": "assistant",
                "content": [{"type": "text", "text": "history result"}],
            }]}
        raise AssertionError(tool)

    async def list_tasks(self, *, session_key, agent_id="main", statuses=None, limit=100):
        return [
            {
                "id": f"task-{index}",
                "runId": f"run-{index}",
                "status": self.task_status,
                "result": f"result for run-{index}",
            }
            for index in range(1, len(self.spawned) + 1)
        ]

    async def cancel_task(self, task_id):
        self.cancelled.append(task_id)
        return {"ok": True}


class _ControlledWaitGateway(_FakeGateway):
    def __init__(self) -> None:
        super().__init__()
        self.wait_started = asyncio.Event()
        self.release_wait = asyncio.Event()

    async def list_tasks(self, *, session_key, agent_id="main", statuses=None, limit=100):
        self.wait_count += 1
        self.wait_started.set()
        await self.release_wait.wait()
        return await super().list_tasks(
            session_key=session_key, agent_id=agent_id, statuses=statuses, limit=limit
        )


class _ControlledSpawnGateway(_FakeGateway):
    def __init__(self) -> None:
        super().__init__()
        self.ensure_started = asyncio.Event()
        self.release_ensure = asyncio.Event()

    async def ensure_session(self, *, session_key, agent_id="main", label="MERRICK Agent Board"):
        self.ensure_started.set()
        await self.release_ensure.wait()
        return await super().ensure_session(
            session_key=session_key, agent_id=agent_id, label=label
        )


class MultiAgentControllerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.gateway = _FakeGateway()
        self.events: list[dict] = []

        async def emit(event):
            self.events.append(event)

        self.controller = MultiAgentRunController(self.gateway, emit)

    async def test_each_work_step_becomes_one_visible_persistent_session(self) -> None:
        run = await self.controller.execute(
            plan_id="plan-1",
            goal="Compare three options",
            steps=[
                {"id": "one", "title": "Option one", "instruction": "Research option one."},
                {"id": "two", "title": "Option two", "instruction": "Research option two."},
                {"id": "three", "title": "Option three", "instruction": "Research option three."},
            ],
            session_key="owner-session",
        )

        self.assertEqual(len(self.gateway.spawned), 3)
        self.assertTrue(all(call["visible"] is True for call in self.gateway.spawned))
        self.assertTrue(all(call["group"] == "MERRICK Agents" for call in self.gateway.spawned))
        self.assertTrue(all("collect" not in call for call in self.gateway.spawned))
        self.assertTrue(all(child.to_dict()["can_open"] for child in run.children))
        self.assertEqual([child.status for child in run.children], ["succeeded"] * 3)
        self.assertEqual(run.status, "synthesizing")
        self.assertEqual(self.events[-1]["run"]["progress"], {
            "completed": 3, "succeeded": 3, "total": 3,
        })

    async def test_board_payload_never_exposes_child_instructions(self) -> None:
        await self.controller.execute(
            plan_id="plan-1",
            goal="One task",
            steps=[{"id": "one", "title": "Private work", "instruction": "secret internal prompt"}],
            session_key="owner-session",
        )

        serialized = str(self.events)
        self.assertNotIn("secret internal prompt", serialized)
        self.assertIn("result for run-1", serialized)

    async def test_cancel_targets_only_tasks_owned_by_the_active_run(self) -> None:
        self.controller.active = None
        # Start just enough state to obtain two accepted run ids, then mark it
        # active to exercise the durable-task cancellation mapping.
        await self.controller.execute(
            plan_id="plan-1",
            goal="Two tasks",
            steps=[
                {"id": "one", "title": "One", "instruction": "Do one."},
                {"id": "two", "title": "Two", "instruction": "Do two."},
            ],
            session_key="owner-session",
        )
        self.controller.active.status = "running"
        for child in self.controller.active.children:
            child.status = "running"

        await self.controller.cancel(session_key="owner-session")

        self.assertEqual(self.gateway.cancelled, ["task-1", "task-2"])
        self.assertEqual(self.controller.active.status, "cancelled")
        self.assertTrue(all(child.status == "cancelled" for child in self.controller.active.children))

    async def test_restart_loads_the_board_and_reconciles_against_the_task_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "multi-agent-run.json"
            original = MultiAgentRunController(self.gateway, self.controller.emit, state_path=state_path)
            await original.execute(
                plan_id="plan-1",
                goal="Recover this run",
                steps=[{"id": "one", "title": "One", "instruction": "Do one."}],
                session_key="owner-session",
            )
            original.active.status = "running"
            original.active.children[0].status = "running"
            original._persist()
            self.gateway.task_status = "failed"

            restored = MultiAgentRunController(self.gateway, self.controller.emit, state_path=state_path)
            await restored.reconcile(session_key="owner-session")

            self.assertEqual(restored.active.status, "failed")
            self.assertEqual(restored.active.children[0].status, "failed")
            self.assertEqual(restored.active.children[0].task_id, "task-1")

    async def test_owner_can_append_a_child_before_the_live_completion_barrier(self) -> None:
        gateway = _ControlledWaitGateway()
        controller = MultiAgentRunController(gateway, self.controller.emit)
        execution = asyncio.create_task(controller.execute(
            plan_id="plan-1",
            goal="Dynamic review",
            steps=[{"id": "one", "title": "First", "instruction": "Do first."}],
            session_key="owner-session",
        ))
        await gateway.wait_started.wait()

        added = await controller.add_child(
            run_id=controller.active.id,
            label="Second",
            instruction="Do second.",
            session_key="owner-session",
        )
        gateway.release_wait.set()
        run = await execution

        self.assertEqual(len(gateway.spawned), 2)
        self.assertEqual(added.status, "succeeded")
        self.assertEqual([child.status for child in run.children], ["succeeded", "succeeded"])
        self.assertEqual(run.status, "synthesizing")

    async def test_owner_can_close_one_child_without_changing_its_sibling(self) -> None:
        gateway = _ControlledWaitGateway()
        controller = MultiAgentRunController(gateway, self.controller.emit)
        execution = asyncio.create_task(controller.execute(
            plan_id="plan-1",
            goal="Selective cancellation",
            steps=[
                {"id": "one", "title": "First", "instruction": "Do first."},
                {"id": "two", "title": "Second", "instruction": "Do second."},
            ],
            session_key="owner-session",
        ))
        await gateway.wait_started.wait()

        cancelled = await controller.close_child(
            run_id=controller.active.id,
            child_id="one",
            session_key="owner-session",
        )
        gateway.release_wait.set()
        run = await execution

        self.assertEqual(cancelled.status, "cancelled")
        self.assertTrue(cancelled.closed)
        self.assertEqual(gateway.archived[0]["sessionKey"], "agent:main:subagent-1")
        self.assertEqual(gateway.archived[0]["expectedSessionId"], "session-1")
        self.assertEqual(run.children[1].status, "succeeded")
        self.assertEqual(run.status, "partial")

    async def test_terminal_agent_can_be_closed_and_keeps_its_result(self) -> None:
        run = await self.controller.execute(
            plan_id="plan-1",
            goal="Close after completion",
            steps=[{"id": "one", "title": "Finished", "instruction": "Finish."}],
            session_key="owner-session",
        )

        child = await self.controller.close_child(
            run_id=run.id, child_id="one", session_key="owner-session"
        )

        self.assertTrue(child.closed)
        self.assertEqual(child.status, "succeeded")
        self.assertEqual(child.result, "result for run-1")
        self.assertFalse(child.to_dict()["can_open"])

    async def test_close_during_spawn_waits_for_upstream_archive_before_hiding(self) -> None:
        gateway = _ControlledSpawnGateway()
        controller = MultiAgentRunController(gateway, self.controller.emit)
        execution = asyncio.create_task(controller.execute(
            plan_id="plan-1",
            goal="Close during creation",
            steps=[{"id": "one", "title": "Starting", "instruction": "Start."}],
            session_key="owner-session",
        ))
        await gateway.ensure_started.wait()

        child = controller.active.children[0]
        close_result = await controller.close_child(
            run_id=controller.active.id,
            child_id=child.id,
            session_key="owner-session",
        )

        self.assertEqual(close_result.status, "cancelling")
        self.assertFalse(close_result.closed)
        gateway.release_ensure.set()
        run = await execution

        self.assertTrue(run.children[0].closed)
        self.assertEqual(run.children[0].status, "cancelled")
        self.assertEqual(gateway.archived[0]["sessionKey"], "agent:main:subagent-1")

    async def test_manual_instruction_never_crosses_the_board_boundary(self) -> None:
        gateway = _ControlledWaitGateway()
        controller = MultiAgentRunController(gateway, self.controller.emit)
        execution = asyncio.create_task(controller.execute(
            plan_id="plan-1",
            goal="Private dynamic review",
            steps=[{"id": "one", "title": "First", "instruction": "Do first."}],
            session_key="owner-session",
        ))
        await gateway.wait_started.wait()
        await controller.add_child(
            run_id=controller.active.id,
            label="Private child",
            instruction="never expose this manual instruction",
            session_key="owner-session",
        )

        self.assertNotIn("never expose this manual instruction", str(self.events))
        gateway.release_wait.set()
        await execution


class MultiAgentRuntimeConfigTests(unittest.TestCase):
    def test_loopback_gateway_exposes_persistent_session_tools(self) -> None:
        template = (PROJECT_ROOT / "openclaw/openclaw.template.json5").read_text(
            encoding="utf-8"
        )

        self.assertIn('tools: { allow: ["sessions_spawn", "sessions_list", "sessions_history", "sessions"] }', template)
        self.assertIn("swarm: {", template)
        self.assertIn("enabled: true", template)


if __name__ == "__main__":
    unittest.main()
