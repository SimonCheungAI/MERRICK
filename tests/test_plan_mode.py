"""Plan Mode domain tests: no gateway, web socket, or macOS host required."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))
from plan_mode import (  # noqa: E402
    PlanModeCoordinator,
    PlanModeError,
    parse_auto_plan_decision,
    parse_plan_draft,
)
import main as main_module  # noqa: E402
from main import Session  # noqa: E402


VALID_PLAN = """```json
{
  "goal": "Compare agentic AI platforms",
  "approaches": [
    {
      "id": "research-first",
      "title": "Research before deciding",
      "summary": "Collect current evidence, then compare it.",
      "recommended": true,
      "execution_mode": "sequential",
      "steps": [
        {"id": "sources", "title": "Collect sources", "detail": "Find primary sources.", "instruction": "Research current agentic AI platforms from primary sources."},
        {"id": "compare", "title": "Compare options", "detail": "Compare the evidence.", "instruction": "Compare the collected platforms and explain the trade-offs."}
      ]
    }
  ]
}
```"""


class PlanDraftParsingTests(unittest.TestCase):
    def test_an_explicit_stepwise_request_requires_a_second_plan_router_pass(self) -> None:
        self.assertTrue(main_module.requires_plan_review_retry(
            "Prepare a three-step internal verification checklist for MERRICK Plan Mode."
        ))

    def test_auto_router_parses_a_structured_plan_without_executing_it(self) -> None:
        decision = parse_auto_plan_decision(
            '{"route":"plan","plan":' + VALID_PLAN.split("```json\n", 1)[1].rsplit("\n```", 1)[0] + '}',
            fallback_goal="Prepare a research brief",
        )

        self.assertEqual(decision.route, "plan")
        self.assertEqual(decision.draft.goal, "Compare agentic AI platforms")

    def test_parses_a_fenced_plan_and_preserves_step_instructions(self) -> None:
        draft = parse_plan_draft(VALID_PLAN, fallback_goal="ignored")

        self.assertEqual(draft.goal, "Compare agentic AI platforms")
        self.assertEqual(draft.status, "draft")
        self.assertEqual(draft.approaches[0].steps[1].instruction, "Compare the collected platforms and explain the trade-offs.")

    def test_rejects_a_partial_plan_without_steps(self) -> None:
        with self.assertRaises(PlanModeError):
            parse_plan_draft('{"goal":"x","approaches":[{"id":"a","title":"A","summary":"B","steps":[]}]}', fallback_goal="x")

    def test_parallel_execution_mode_is_preserved_and_unknown_modes_are_safe(self) -> None:
        parallel = VALID_PLAN.replace('"execution_mode": "sequential"', '"execution_mode": "parallel"')
        self.assertEqual(
            parse_plan_draft(parallel, fallback_goal="ignored").approaches[0].execution_mode,
            "parallel",
        )
        unknown = VALID_PLAN.replace('"execution_mode": "sequential"', '"execution_mode": "distributed"')
        self.assertEqual(
            parse_plan_draft(unknown, fallback_goal="ignored").approaches[0].execution_mode,
            "sequential",
        )


class PlanModeCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events: list[dict] = []
        self.coordinator = PlanModeCoordinator(self.events.append)
        self.coordinator.load_draft(parse_plan_draft(VALID_PLAN, fallback_goal="ignored"))

    def test_selecting_an_approach_only_updates_plan_state(self) -> None:
        state = self.coordinator.select("research-first")

        self.assertEqual(state.status, "ready")
        self.assertEqual(state.selected_approach_id, "research-first")
        self.assertEqual(self.events[-1]["type"], "plan_mode_state")

    def test_run_next_advances_exactly_one_step(self) -> None:
        self.coordinator.select("research-first")
        step = self.coordinator.start_next()
        self.coordinator.finish_step(step.id, result="Sources collected.")

        state = self.coordinator.snapshot()
        self.assertEqual(step.id, "sources")
        self.assertEqual(state.approaches[0].steps[0].status, "succeeded")
        self.assertEqual(state.approaches[0].steps[1].status, "planned")

    def test_binding_selected_steps_to_organizer_records_preserves_the_mapping(self) -> None:
        self.coordinator.select("research-first")
        state = self.coordinator.bind_organizer_records(
            "project-plan-ai",
            {"sources": "task-sources", "compare": "task-compare"},
        )

        self.assertEqual(state.organizer_project_id, "project-plan-ai")
        self.assertEqual(state.approaches[0].steps[0].organizer_task_id, "task-sources")

    def test_cancelling_prevents_a_later_step_from_starting(self) -> None:
        self.coordinator.select("research-first")
        self.coordinator.cancel()

        with self.assertRaises(PlanModeError):
            self.coordinator.start_next()

    def test_parallel_start_keeps_plan_running_until_every_step_finishes(self) -> None:
        draft = parse_plan_draft(
            VALID_PLAN.replace('"execution_mode": "sequential"', '"execution_mode": "parallel"'),
            fallback_goal="ignored",
        )
        self.coordinator.load_draft(draft)
        self.coordinator.select("research-first")

        started = self.coordinator.start_all_pending()
        self.assertEqual([step.id for step in started], ["sources", "compare"])
        self.coordinator.finish_step("sources", result="Sources collected.")

        state = self.coordinator.snapshot()
        self.assertEqual(state.status, "running")
        self.assertEqual(state.approaches[0].steps[0].status, "succeeded")
        self.assertEqual(state.approaches[0].steps[1].status, "running")


class _FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_text(self, raw: str) -> None:
        self.messages.append(json.loads(raw))


class PlanModeSessionIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ws = _FakeWebSocket()
        self.session = Session(self.ws)  # type: ignore[arg-type]
        self.multi_agent_tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.multi_agent_tempdir.cleanup)
        self.session.multi_agent = main_module.MultiAgentRunController(
            main_module.openclaw_gateway,
            self.session.send,
            state_path=Path(self.multi_agent_tempdir.name) / "multi-agent-run.json",
        )
        self.session.tts_enabled = False
        self.session.plan_mode.load_draft(parse_plan_draft(VALID_PLAN, fallback_goal="ignored"))
        self.created_tasks: list[dict] = []

        self.session.organizer.create_project = lambda title: {"id": "project-plan-ai", "title": title}  # type: ignore[method-assign]

        def create_task(title: str, *, project_title: str = "", source: str = "user") -> dict:
            self.created_tasks.append({"title": title, "project_title": project_title, "source": source})
            return {"id": f"task-{len(self.created_tasks)}", "title": title}

        self.session.organizer.create_task = create_task  # type: ignore[method-assign]
        self.session.organizer.complete_task = lambda task_id: {"id": task_id}  # type: ignore[method-assign]
        self.session.send_organizer_snapshot = AsyncMock()  # type: ignore[method-assign]
        await asyncio.sleep(0)

    async def test_selecting_a_plan_emits_only_plan_state(self) -> None:
        plan_id = self.session.plan_mode.snapshot().id
        self.ws.messages.clear()
        await self.session.handle_message({
            "type": "plan_mode_select", "plan_id": plan_id, "approach_id": "research-first",
        })
        await asyncio.sleep(0)

        self.assertTrue(any(message["type"] == "plan_mode_state" for message in self.ws.messages))
        self.assertFalse(any(message["type"] == "assistant_delta" for message in self.ws.messages))
        self.assertEqual([task["title"] for task in self.created_tasks], ["Collect sources", "Compare options"])
        self.assertEqual(self.session.plan_mode.snapshot().organizer_project_id, "project-plan-ai")

    async def test_run_next_uses_existing_main_query_and_advances_one_step(self) -> None:
        plan_id = self.session.plan_mode.snapshot().id
        await self.session.handle_message({
            "type": "plan_mode_select", "plan_id": plan_id, "approach_id": "research-first",
        })
        await asyncio.sleep(0)
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        await self.session.handle_message({"type": "plan_mode_run", "plan_id": plan_id, "mode": "next"})
        assert self.session.query_task is not None
        await self.session.query_task
        await asyncio.sleep(0)

        self.session.run_query.assert_awaited_once()  # type: ignore[attr-defined]
        state = self.session.plan_mode.snapshot()
        selected = state.approaches[0]
        self.assertEqual(selected.steps[0].status, "succeeded")
        self.assertEqual(selected.steps[1].status, "planned")

    async def test_parallel_run_all_spawns_persistent_agents_and_synthesizes_once(self) -> None:
        self.session.plan_mode.load_draft(parse_plan_draft(
            VALID_PLAN.replace('"execution_mode": "sequential"', '"execution_mode": "parallel"'),
            fallback_goal="ignored",
        ))
        plan_id = self.session.plan_mode.snapshot().id
        await self.session.handle_message({
            "type": "plan_mode_select", "plan_id": plan_id, "approach_id": "research-first",
        })
        await asyncio.sleep(0)
        spawn_count = 0

        async def invoke_rpc(tool, args, **_kwargs):
            nonlocal spawn_count
            if tool == "sessions_spawn":
                spawn_count += 1
                return {
                    "status": "accepted",
                    "runId": f"run-{spawn_count}",
                    "childSessionKey": f"agent:main:child-{spawn_count}",
                    "sessionUrl": f"http://127.0.0.1:18789/#/sessions/child-{spawn_count}",
                }
            raise AssertionError(tool)

        async def list_tasks(**_kwargs):
            return [
                {
                    "id": f"task-{index}",
                    "runId": f"run-{index}",
                    "status": "succeeded",
                    "result": f"evidence run-{index}",
                }
                for index in range(1, spawn_count + 1)
            ]

        async def summary_response(*_args, **_kwargs):
            yield "The two agents completed their independent work."

        self.ws.messages.clear()
        with (
            patch.object(main_module.openclaw_gateway, "ensure_session", new=AsyncMock()),
            patch.object(main_module.openclaw_gateway, "invoke_rpc_tool", new=invoke_rpc),
            patch.object(main_module.openclaw_gateway, "list_tasks", new=list_tasks),
            patch.object(main_module.openclaw_gateway, "stream_response", new=summary_response),
        ):
            await self.session.handle_message({"type": "plan_mode_run", "plan_id": plan_id, "mode": "all"})
            assert self.session.query_task is not None
            await self.session.query_task
        await asyncio.sleep(0)

        self.assertEqual(spawn_count, 2)
        self.assertEqual(self.session.plan_mode.snapshot().status, "succeeded")
        self.assertTrue(any(
            message.get("type") == "multi_agent_state"
            and message.get("run", {}).get("status") == "succeeded"
            for message in self.ws.messages
        ))
        self.assertEqual(
            "".join(message.get("text", "") for message in self.ws.messages if message.get("type") == "assistant_delta"),
            "The two agents completed their independent work.",
        )

    async def test_agent_board_can_schedule_a_manual_agent_without_blocking_messages(self) -> None:
        self.session.start_or_append_manual_agent = AsyncMock()  # type: ignore[method-assign]

        await self.session.handle_message({
            "type": "multi_agent_spawn",
            "run_id": "",
            "label": "Security reviewer",
            "task": "Review the authentication path.",
        })
        await asyncio.sleep(0)

        self.session.start_or_append_manual_agent.assert_awaited_once_with(  # type: ignore[attr-defined]
            run_id="",
            label="Security reviewer",
            instruction="Review the authentication path.",
        )

    async def test_agent_board_can_schedule_one_exact_child_close(self) -> None:
        self.session.close_manual_agent = AsyncMock()  # type: ignore[method-assign]

        await self.session.handle_message({
            "type": "multi_agent_close_child",
            "run_id": "run-1",
            "child_id": "child-2",
        })
        await asyncio.sleep(0)

        self.session.close_manual_agent.assert_awaited_once_with(  # type: ignore[attr-defined]
            run_id="run-1",
            child_id="child-2",
        )

    async def test_agent_board_rejects_blank_manual_agent_input(self) -> None:
        self.ws.messages.clear()

        await self.session.handle_message({
            "type": "multi_agent_spawn", "run_id": "", "label": "", "task": ""
        })

        self.assertTrue(any(
            message.get("type") == "multi_agent_error"
            and message.get("code") == "AGENT_INPUT_INVALID"
            for message in self.ws.messages
        ))

    async def test_a_segmented_spoken_task_opens_a_plan_instead_of_executing_it(self) -> None:
        async def planned_response(*_args, **_kwargs):
            yield '{"route":"plan","plan":' + VALID_PLAN.split("```json\n", 1)[1].rsplit("\n```", 1)[0] + '}'

        self.session.run_query = AsyncMock()  # type: ignore[method-assign]
        self.ws.messages.clear()

        with patch.object(main_module.openclaw_gateway, "stream_response", new=planned_response):
            await self.session.route_auto_plan_or_query(
                "Research agentic AI and prepare a detailed comparison for me.",
                is_draft=False,
                trusted_typed=True,
                detect_action=True,
            )
        await asyncio.sleep(0)

        self.session.run_query.assert_not_awaited()  # type: ignore[attr-defined]
        self.assertEqual(self.session.plan_mode.snapshot().goal, "Compare agentic AI platforms")
        self.assertTrue(any(message["type"] == "plan_mode_state" for message in self.ws.messages))
        self.assertTrue(any(
            message.get("type") == "status" and message.get("state") == "idle"
            for message in self.ws.messages
        ))

    async def test_a_direct_router_decision_preserves_the_existing_query_path(self) -> None:
        async def direct_response(*_args, **_kwargs):
            yield '{"route":"direct"}'

        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        with patch.object(main_module.openclaw_gateway, "stream_response", new=direct_response):
            await self.session.route_auto_plan_or_query(
                "Open Chrome and search for a local cafe.",
                is_draft=False,
                trusted_typed=True,
                detect_action=True,
            )

        self.session.run_query.assert_awaited_once()  # type: ignore[attr-defined]
        self.assertEqual(self.session.plan_mode.snapshot().goal, "Compare agentic AI platforms")

    async def test_an_explicit_stepwise_request_retries_direct_router_output_as_a_plan(self) -> None:
        responses = iter([
            '{"route":"direct"}',
            '{"route":"plan","plan":' + VALID_PLAN.split("```json\n", 1)[1].rsplit("\n```", 1)[0] + '}',
        ])
        calls: list[dict] = []

        async def retried_response(*_args, **kwargs):
            calls.append(kwargs)
            yield next(responses)

        self.session.run_query = AsyncMock()  # type: ignore[method-assign]
        with patch.object(main_module.openclaw_gateway, "stream_response", new=retried_response):
            await self.session.route_auto_plan_or_query(
                "Prepare a three-step internal verification checklist for MERRICK Plan Mode.",
                is_draft=False,
                trusted_typed=True,
                detect_action=True,
            )

        self.assertEqual(len(calls), 2)
        self.session.run_query.assert_not_awaited()  # type: ignore[attr-defined]
        self.assertEqual(self.session.plan_mode.snapshot().goal, "Compare agentic AI platforms")


if __name__ == "__main__":
    unittest.main()
