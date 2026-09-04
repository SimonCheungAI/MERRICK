"""Domain state for MERRICK Plan Mode.

This module deliberately has no FastAPI, WebSocket, native-host, or OpenClaw
imports.  The session supplies those adapters at its boundary, which keeps
planning, selection, and ordered step transitions testable in isolation.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, replace
from typing import Callable, Iterable


class PlanModeError(ValueError):
    """A recoverable Plan Mode request or model-output error."""


PLAN_STATUSES = frozenset({
    "draft", "ready", "running", "succeeded", "failed", "cancelled", "blocked",
})
STEP_STATUSES = frozenset({"planned", "running", "succeeded", "failed", "cancelled", "blocked"})
EXECUTION_MODES = frozenset({"sequential", "parallel"})


@dataclass(frozen=True)
class PlanStep:
    id: str
    title: str
    detail: str
    instruction: str
    status: str = "planned"
    result: str = ""
    organizer_task_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "detail": self.detail,
            "instruction": self.instruction,
            "status": self.status,
            "result": self.result,
            "organizer_task_id": self.organizer_task_id,
        }


@dataclass(frozen=True)
class PlanApproach:
    id: str
    title: str
    summary: str
    recommended: bool
    steps: tuple[PlanStep, ...]
    execution_mode: str = "sequential"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "recommended": self.recommended,
            "execution_mode": self.execution_mode,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(frozen=True)
class PlanDraft:
    id: str
    goal: str
    approaches: tuple[PlanApproach, ...]
    selected_approach_id: str | None = None
    organizer_project_id: str = ""
    status: str = "draft"

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "goal": self.goal,
            "approaches": [approach.to_dict() for approach in self.approaches],
            "selected_approach_id": self.selected_approach_id,
            "organizer_project_id": self.organizer_project_id,
            "status": self.status,
        }


@dataclass(frozen=True)
class AutoPlanDecision:
    """The tool-free planner's routing outcome for one eligible work turn."""

    route: str
    draft: PlanDraft | None = None


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not (text := value.strip()):
        raise PlanModeError(f"Plan field '{field}' must be a non-empty string.")
    return text


def _json_object(raw: str) -> dict[str, object]:
    source = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", source, re.DOTALL | re.IGNORECASE)
    if fenced:
        source = fenced.group(1)
    else:
        start, end = source.find("{"), source.rfind("}")
        if start < 0 or end <= start:
            raise PlanModeError("The planner did not return a structured plan.")
        source = source[start:end + 1]
    try:
        parsed = json.loads(source)
    except json.JSONDecodeError as exc:
        raise PlanModeError("The planner returned invalid plan JSON.") from exc
    if not isinstance(parsed, dict):
        raise PlanModeError("The planner returned an invalid plan object.")
    return parsed


def parse_plan_draft(raw: str, *, fallback_goal: str) -> PlanDraft:
    """Parse the planner's structural JSON without applying an action policy."""
    payload = _json_object(raw)
    goal = _text(payload.get("goal", fallback_goal), "goal")
    raw_approaches = payload.get("approaches")
    if not isinstance(raw_approaches, list) or not 1 <= len(raw_approaches) <= 3:
        raise PlanModeError("A plan needs one to three approaches.")

    approaches: list[PlanApproach] = []
    approach_ids: set[str] = set()
    for index, raw_approach in enumerate(raw_approaches, start=1):
        if not isinstance(raw_approach, dict):
            raise PlanModeError("Each approach must be an object.")
        approach_id = _text(raw_approach.get("id", f"approach-{index}"), "approach.id")
        if approach_id in approach_ids:
            raise PlanModeError("Plan approach identifiers must be unique.")
        approach_ids.add(approach_id)
        raw_steps = raw_approach.get("steps")
        if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= 8:
            raise PlanModeError("Each approach needs one to eight steps.")
        step_ids: set[str] = set()
        steps: list[PlanStep] = []
        for step_index, raw_step in enumerate(raw_steps, start=1):
            if not isinstance(raw_step, dict):
                raise PlanModeError("Each plan step must be an object.")
            step_id = _text(raw_step.get("id", f"step-{step_index}"), "step.id")
            if step_id in step_ids:
                raise PlanModeError("Step identifiers must be unique within an approach.")
            step_ids.add(step_id)
            steps.append(PlanStep(
                id=step_id,
                title=_text(raw_step.get("title"), "step.title"),
                detail=_text(raw_step.get("detail"), "step.detail"),
                instruction=_text(raw_step.get("instruction"), "step.instruction"),
            ))
        approaches.append(PlanApproach(
            id=approach_id,
            title=_text(raw_approach.get("title"), "approach.title"),
            summary=_text(raw_approach.get("summary"), "approach.summary"),
            recommended=raw_approach.get("recommended") is True,
            steps=tuple(steps),
            execution_mode=(
                raw_approach.get("execution_mode")
                if raw_approach.get("execution_mode") in EXECUTION_MODES
                else "sequential"
            ),
        ))
    return PlanDraft(id=uuid.uuid4().hex, goal=goal, approaches=tuple(approaches))


def parse_auto_plan_decision(raw: str, *, fallback_goal: str) -> AutoPlanDecision:
    """Parse a direct-or-plan decision without invoking tools or transport."""
    payload = _json_object(raw)
    route = payload.get("route")
    if route == "direct":
        return AutoPlanDecision(route="direct")
    if route != "plan":
        raise PlanModeError("The planner returned an invalid routing decision.")
    plan_payload = payload.get("plan")
    if not isinstance(plan_payload, dict):
        raise PlanModeError("The planner did not include a structured plan.")
    return AutoPlanDecision(
        route="plan",
        draft=parse_plan_draft(json.dumps(plan_payload), fallback_goal=fallback_goal),
    )


class PlanModeCoordinator:
    """Own per-session draft selection and ordered step state transitions."""

    def __init__(self, emit: Callable[[dict[str, object]], object]) -> None:
        self._emit = emit
        self._draft: PlanDraft | None = None

    def snapshot(self) -> PlanDraft:
        if self._draft is None:
            raise PlanModeError("There is no active plan.")
        return self._draft

    def load_draft(self, draft: PlanDraft) -> PlanDraft:
        self._draft = draft
        self._emit_state()
        return draft

    def select(self, approach_id: str) -> PlanDraft:
        draft = self.snapshot()
        if draft.status not in {"draft", "ready"}:
            raise PlanModeError("This plan can no longer be selected.")
        if not any(approach.id == approach_id for approach in draft.approaches):
            raise PlanModeError("That plan approach is no longer available.")
        self._draft = replace(draft, selected_approach_id=approach_id, status="ready")
        self._emit_state()
        return self._draft

    def bind_organizer_records(
        self, project_id: str, task_ids_by_step_id: dict[str, str]
    ) -> PlanDraft:
        """Attach live Organizer record ids after the user accepts an approach."""
        draft = self.snapshot()
        approach = self._selected_approach(draft)
        expected_ids = {step.id for step in approach.steps}
        if not project_id or set(task_ids_by_step_id) != expected_ids:
            raise PlanModeError("The selected plan could not be linked to its work records.")
        updated_approach = replace(
            approach,
            steps=tuple(
                replace(step, organizer_task_id=task_ids_by_step_id[step.id])
                for step in approach.steps
            ),
        )
        self._draft = replace(
            draft,
            organizer_project_id=project_id,
            approaches=tuple(
                updated_approach if item.id == approach.id else item
                for item in draft.approaches
            ),
        )
        self._emit_state()
        return self._draft

    def start_next(self) -> PlanStep:
        draft = self.snapshot()
        if draft.status not in {"ready", "running"} or not draft.selected_approach_id:
            raise PlanModeError("Choose a plan approach before running it.")
        approach = self._selected_approach(draft)
        step = next((item for item in approach.steps if item.status == "planned"), None)
        if step is None:
            raise PlanModeError("There is no pending plan step to run.")
        running = replace(step, status="running", result="")
        self._draft = replace(
            draft,
            approaches=tuple(
                self._replace_approach_step(item, running) if item.id == approach.id else item
                for item in draft.approaches
            ),
            status="running",
        )
        self._emit_step(running)
        self._emit_state()
        return running

    def start_all_pending(self) -> tuple[PlanStep, ...]:
        """Start every pending step for one explicitly parallel approach."""
        draft = self.snapshot()
        if draft.status not in {"ready", "running"} or not draft.selected_approach_id:
            raise PlanModeError("Choose a plan approach before running it.")
        approach = self._selected_approach(draft)
        if approach.execution_mode != "parallel":
            raise PlanModeError("That plan approach is not parallel.")
        pending = tuple(item for item in approach.steps if item.status == "planned")
        if not pending:
            raise PlanModeError("There are no pending plan steps to run.")
        running_by_id = {
            item.id: replace(item, status="running", result="")
            for item in pending
        }
        updated_approach = replace(
            approach,
            steps=tuple(running_by_id.get(item.id, item) for item in approach.steps),
        )
        self._draft = replace(
            draft,
            approaches=tuple(
                updated_approach if item.id == approach.id else item
                for item in draft.approaches
            ),
            status="running",
        )
        for running in running_by_id.values():
            self._emit_step(running)
        self._emit_state()
        return tuple(running_by_id[item.id] for item in pending)

    def finish_step(self, step_id: str, *, result: str = "", status: str = "succeeded") -> PlanDraft:
        if status not in {"succeeded", "failed", "blocked", "cancelled"}:
            raise PlanModeError("Plan step finished with an invalid status.")
        draft = self.snapshot()
        approach = self._selected_approach(draft)
        current = next((item for item in approach.steps if item.id == step_id), None)
        if current is None or current.status != "running":
            raise PlanModeError("That plan step is not running.")
        finished = replace(current, status=status, result=result.strip())
        updated_approach = self._replace_approach_step(approach, finished)
        statuses = {item.status for item in updated_approach.steps}
        if statuses == {"succeeded"}:
            plan_status = "succeeded"
        elif "running" in statuses:
            plan_status = "running"
        elif "failed" in statuses:
            plan_status = "failed"
        elif "blocked" in statuses:
            plan_status = "blocked"
        elif "cancelled" in statuses:
            plan_status = "cancelled"
        else:
            plan_status = "ready"
        self._draft = replace(
            draft,
            approaches=tuple(updated_approach if item.id == approach.id else item for item in draft.approaches),
            status=plan_status,
        )
        self._emit_step(finished)
        self._emit_state()
        return self._draft

    def cancel(self) -> PlanDraft:
        draft = self.snapshot()
        if draft.status in {"succeeded", "failed", "blocked", "cancelled"}:
            return draft
        approaches = tuple(
            replace(
                approach,
                steps=tuple(
                    replace(step, status="cancelled") if step.status == "running" else step
                    for step in approach.steps
                ),
            ) if approach.id == draft.selected_approach_id else approach
            for approach in draft.approaches
        )
        self._draft = replace(draft, approaches=approaches, status="cancelled")
        self._emit_state()
        return self._draft

    def _selected_approach(self, draft: PlanDraft) -> PlanApproach:
        approach = next((item for item in draft.approaches if item.id == draft.selected_approach_id), None)
        if approach is None:
            raise PlanModeError("Choose a plan approach before running it.")
        return approach

    @staticmethod
    def _replace_approach_step(approach: PlanApproach, updated: PlanStep) -> PlanApproach:
        return replace(
            approach,
            steps=tuple(updated if step.id == updated.id else step for step in approach.steps),
        )

    def _emit_step(self, step: PlanStep) -> None:
        draft = self.snapshot()
        self._emit({
            "type": "plan_mode_step",
            "plan_id": draft.id,
            "step_id": step.id,
            "status": step.status,
            "result": step.result,
        })

    def _emit_state(self) -> None:
        draft = self.snapshot()
        self._emit({"type": "plan_mode_state", "status": draft.status, "plan": draft.to_dict()})
