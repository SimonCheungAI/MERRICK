"""Truthful, observable orchestration for persistent OpenClaw agent sessions."""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from pathlib import Path


MAX_CHILDREN = 8
MAX_RESULT_CHARS = 12_000
TASK_POLL_SECONDS = 0.25
TASK_WAIT_SECONDS = 330.0
TERMINAL_CHILD_STATES = frozenset({"succeeded", "failed", "cancelled", "timed_out"})
SAFE_TASK_NAME_RE = re.compile(r"[^a-z0-9_-]+")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _bounded_text(value: object, *, limit: int = MAX_RESULT_CHARS) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class MultiAgentGateway(Protocol):
    async def ensure_session(
        self,
        *,
        session_key: str,
        agent_id: str = "main",
        label: str = "MERRICK Agent Board",
    ) -> dict: ...

    async def invoke_rpc_tool(
        self,
        tool: str,
        args: dict,
        *,
        session_key: str,
        agent_id: str = "main",
        timeout: float = 30.0,
    ) -> dict: ...

    async def list_tasks(
        self,
        *,
        session_key: str,
        agent_id: str = "main",
        statuses: Sequence[str] | None = None,
        limit: int = 100,
    ) -> list[dict]: ...

    async def cancel_task(self, task_id: str) -> dict: ...


class MultiAgentControlError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class MultiAgentChild:
    id: str
    label: str
    instruction: str = field(repr=False)
    status: str = "queued"
    run_id: str = ""
    session_key: str = ""
    task_id: str = ""
    session_url: str = ""
    session_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    result: str = ""
    error: str = ""
    cancel_requested: bool = field(default=False, repr=False)
    close_requested: bool = field(default=False, repr=False)
    closed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "run_id": self.run_id,
            "session_key": self.session_key,
            "task_id": self.task_id,
            "session_url": self.session_url,
            "can_open": bool(self.session_url) and not self.closed,
            "closed": self.closed,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class MultiAgentRun:
    id: str
    plan_id: str
    group_id: str
    goal: str
    children: list[MultiAgentChild]
    status: str = "starting"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    summary: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        terminal = sum(child.status in TERMINAL_CHILD_STATES for child in self.children)
        succeeded = sum(child.status == "succeeded" for child in self.children)
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "group_id": self.group_id,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "summary": self.summary,
            "error": self.error,
            "progress": {
                "completed": terminal,
                "succeeded": succeeded,
                "total": len(self.children),
            },
            "children": [child.to_dict() for child in self.children],
        }


class MultiAgentRunController:
    """Spawn independent children, wait for real terminal results, and cancel safely."""

    def __init__(
        self,
        gateway: MultiAgentGateway,
        emit: Callable[[dict[str, Any]], Awaitable[None]],
        *,
        state_path: Path | None = None,
    ) -> None:
        self.gateway = gateway
        self.emit = emit
        self.state_path = state_path
        self.active: MultiAgentRun | None = self._load()
        self._cancel_requested = False
        self._lock = asyncio.Lock()

    def snapshot(self) -> dict[str, Any] | None:
        return self.active.to_dict() if self.active else None

    def _load(self) -> MultiAgentRun | None:
        if self.state_path is None:
            return None
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict) or not isinstance(payload.get("children"), list):
            return None
        try:
            children = [
                MultiAgentChild(
                    id=str(item["id"]),
                    label=str(item["label"]),
                    instruction="",
                    status=str(item.get("status") or "queued"),
                    run_id=str(item.get("run_id") or ""),
                    session_key=str(item.get("session_key") or ""),
                    task_id=str(item.get("task_id") or ""),
                    session_url=str(item.get("session_url") or ""),
                    session_id=str(item.get("session_id") or ""),
                    closed=bool(item.get("closed", False)),
                    started_at=str(item.get("started_at") or ""),
                    ended_at=str(item.get("ended_at") or ""),
                    result=_bounded_text(item.get("result")),
                    error=_bounded_text(item.get("error"), limit=2_000),
                )
                for item in payload["children"]
                if isinstance(item, dict) and item.get("id") and item.get("label")
            ]
            if not children:
                return None
            return MultiAgentRun(
                id=str(payload["id"]),
                plan_id=str(payload.get("plan_id") or ""),
                group_id=str(payload.get("group_id") or ""),
                goal=_bounded_text(payload.get("goal"), limit=500),
                children=children,
                status=str(payload.get("status") or "failed"),
                created_at=str(payload.get("created_at") or _now_iso()),
                updated_at=str(payload.get("updated_at") or _now_iso()),
                summary=_bounded_text(payload.get("summary")),
                error=_bounded_text(payload.get("error"), limit=2_000),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _persist(self) -> None:
        if self.state_path is None or self.active is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.active.to_dict(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(self.state_path)

    async def _emit(self) -> None:
        if self.active is None:
            return
        self.active.updated_at = _now_iso()
        self._persist()
        await self.emit({"type": "multi_agent_state", "run": self.active.to_dict()})

    @staticmethod
    def _message_text(message: object) -> str:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            return ""
        content = message.get("content")
        if isinstance(content, str):
            return _bounded_text(content)
        if not isinstance(content, list):
            return ""
        parts = [
            str(block.get("text") or "")
            for block in content
            if isinstance(block, dict)
            and block.get("type") in {"text", "output_text"}
            and block.get("text")
        ]
        return _bounded_text("\n".join(parts))

    async def _recover_session_result(
        self, child: MultiAgentChild, *, session_key: str
    ) -> None:
        if child.result or not child.session_key:
            return
        history = await self.gateway.invoke_rpc_tool(
            "sessions_history",
            {"sessionKey": child.session_key, "limit": 12, "includeTools": False},
            session_key=session_key,
            timeout=15.0,
        )
        messages = history.get("messages")
        if not isinstance(messages, list):
            return
        for message in reversed(messages):
            text = self._message_text(message)
            if text:
                child.result = text
                return

    async def _apply_task_state(
        self, child: MultiAgentChild, task: dict[str, Any], *, session_key: str
    ) -> None:
        status_map = {
            "queued": "queued", "running": "running", "completed": "succeeded",
            "done": "succeeded", "succeeded": "succeeded", "failed": "failed",
            "lost": "failed", "cancelled": "cancelled", "timed_out": "timed_out",
        }
        child.task_id = str(task.get("id") or task.get("taskId") or child.task_id)
        child.status = status_map.get(str(task.get("status") or ""), child.status)
        summary = task.get("summary") or task.get("result") or task.get("output")
        error = task.get("error") or task.get("errorText")
        if summary:
            child.result = _bounded_text(summary)
        if error:
            child.error = _bounded_text(error, limit=2_000)
        child.started_at = str(task.get("startedAt") or child.started_at)
        if child.status in TERMINAL_CHILD_STATES:
            child.ended_at = str(
                task.get("finishedAt") or task.get("updatedAt") or child.ended_at or _now_iso()
            )
            if child.status == "succeeded" and not child.result:
                try:
                    await self._recover_session_result(child, session_key=session_key)
                except Exception:
                    # The durable task outcome remains authoritative even if the
                    # bounded transcript projection is temporarily unavailable.
                    pass

    async def reconcile(self, *, session_key: str) -> MultiAgentRun | None:
        """Refresh a restored board from OpenClaw's durable task ledger."""
        if self.active is None:
            await self.emit({"type": "multi_agent_state", "run": None})
            return None
        if self.active.status not in {"starting", "running", "cancelling", "synthesizing"}:
            await self._emit()
            return self.active
        tasks = await self.gateway.list_tasks(session_key=session_key, limit=250)
        by_run = {
            str(task.get("runId") or task.get("run_id") or ""): task
            for task in tasks
            if isinstance(task, dict)
        }
        for child in self.active.children:
            task = by_run.get(child.run_id)
            if task is None:
                continue
            await self._apply_task_state(child, task, session_key=session_key)
        aggregate = self._aggregate_status()
        self.active.status = "succeeded" if aggregate == "synthesizing" else aggregate
        await self._emit()
        return self.active

    @staticmethod
    def _task_name(index: int, child_id: str) -> str:
        slug = SAFE_TASK_NAME_RE.sub("-", child_id.lower()).strip("-")[:40]
        return f"jarvis-agent-{index + 1}-{slug or 'task'}"[:64]

    async def _archive_child_upstream(
        self, child: MultiAgentChild, *, session_key: str
    ) -> None:
        if not child.session_key:
            raise MultiAgentControlError(
                "ARCHIVE_FAILED", "OpenClaw has not published this agent session yet."
            )
        listed = await self.gateway.invoke_rpc_tool(
            "sessions_list",
            {"limit": 200},
            session_key=session_key,
            timeout=15.0,
        )
        rows = listed.get("sessions")
        row = next(
            (
                item for item in rows
                if isinstance(item, dict) and str(item.get("key") or "") == child.session_key
            ),
            None,
        ) if isinstance(rows, list) else None
        if row is None:
            archived = await self.gateway.invoke_rpc_tool(
                "sessions_list",
                {"limit": 200, "archived": True},
                session_key=session_key,
                timeout=15.0,
            )
            archived_rows = archived.get("sessions")
            if isinstance(archived_rows, list) and any(
                isinstance(item, dict) and str(item.get("key") or "") == child.session_key
                for item in archived_rows
            ):
                return
            raise MultiAgentControlError(
                "SESSION_GENERATION_STALE",
                "That OpenClaw session is no longer the session shown on this card.",
            )
        durable_id = str(row.get("sessionId") or "")
        if not durable_id:
            raise MultiAgentControlError(
                "ARCHIVE_FAILED", "OpenClaw did not return the session's durable identity."
            )
        child.session_id = durable_id
        await self.gateway.invoke_rpc_tool(
            "sessions",
            {
                "action": "patch",
                "sessionKey": child.session_key,
                "archived": True,
                "expectedSessionId": durable_id,
            },
            session_key=session_key,
            timeout=30.0,
        )

    async def _spawn_child(
        self,
        child: MultiAgentChild,
        *,
        index: int,
        session_key: str,
    ) -> None:
        if self._cancel_requested or child.cancel_requested or child.close_requested:
            child.status = "cancelled"
            child.ended_at = _now_iso()
            child.closed = child.close_requested
            await self._emit()
            return
        child.status = "starting"
        child.started_at = _now_iso()
        await self._emit()
        try:
            await self.gateway.ensure_session(
                session_key=session_key,
                label="MERRICK Agent Board",
            )
            spawned = await self.gateway.invoke_rpc_tool(
                "sessions_spawn",
                {
                    "task": child.instruction,
                    "taskName": self._task_name(index, child.id),
                    "label": child.label,
                    "visible": True,
                    "group": "MERRICK Agents",
                    "context": "isolated",
                    "runTimeoutSeconds": 300,
                },
                session_key=session_key,
                timeout=30.0,
            )
            child.run_id = _bounded_text(spawned.get("runId"), limit=160)
            child.session_key = _bounded_text(
                spawned.get("childSessionKey") or spawned.get("sessionKey"), limit=240,
            )
            child.task_id = _bounded_text(
                spawned.get("taskId") or spawned.get("task_id"), limit=160,
            )
            child.session_url = _bounded_text(spawned.get("sessionUrl"), limit=2_048)
            if (
                spawned.get("status") != "accepted"
                or not child.run_id
                or not child.session_key
            ):
                raise RuntimeError(
                    _bounded_text(spawned.get("error"))
                    or "OpenClaw did not accept this agent."
                )
            if self._cancel_requested or child.cancel_requested or child.close_requested:
                child.status = "cancelling"
                await self._emit()
                await self._archive_child_upstream(child, session_key=session_key)
                child.status = "cancelled"
                child.ended_at = _now_iso()
                child.closed = True
            else:
                child.status = "running"
        except Exception as exc:
            child.status = "failed"
            child.error = _bounded_text(exc, limit=2_000)
            child.ended_at = _now_iso()
        await self._emit()

    async def add_child(
        self,
        *,
        run_id: str,
        label: str,
        instruction: str,
        session_key: str,
    ) -> MultiAgentChild:
        """Append one owner-authored persistent session before the completion barrier."""
        clean_label = label.strip()
        clean_instruction = instruction.strip()
        if not clean_label or len(clean_label) > 120:
            raise MultiAgentControlError(
                "AGENT_INPUT_INVALID", "Agent name must be between 1 and 120 characters."
            )
        if not clean_instruction or len(clean_instruction) > 4_000:
            raise MultiAgentControlError(
                "AGENT_INPUT_INVALID", "Agent task must be between 1 and 4,000 characters."
            )
        async with self._lock:
            active = self.active
            if active is None or active.id != run_id or active.status not in {"starting", "running"}:
                raise MultiAgentControlError(
                    "RUN_STALE", "That agent run is no longer accepting new agents."
                )
            if len(active.children) >= MAX_CHILDREN:
                raise MultiAgentControlError(
                    "RUN_CAPACITY", f"A run can contain at most {MAX_CHILDREN} agents."
                )
            child = MultiAgentChild(
                id=f"manual-{uuid.uuid4().hex[:12]}",
                label=clean_label,
                instruction=clean_instruction,
            )
            active.children.append(child)
            index = len(active.children) - 1
        await self._emit()
        await self._spawn_child(child, index=index, session_key=session_key)
        return child

    async def close_child(
        self,
        *,
        run_id: str,
        child_id: str,
        session_key: str,
    ) -> MultiAgentChild:
        """Archive one exact persistent child without changing any sibling state."""
        async with self._lock:
            active = self.active
            if active is None or active.id != run_id:
                raise MultiAgentControlError("RUN_STALE", "That agent run is no longer active.")
            child = next((item for item in active.children if item.id == child_id), None)
            if child is None or child.closed:
                raise MultiAgentControlError("CHILD_STALE", "That agent is already closed.")
            child.close_requested = True
            previous_status = child.status
            if child.status not in TERMINAL_CHILD_STATES:
                child.status = "cancelling"
        await self._emit()
        if not child.run_id:
            # `_spawn_child` owns the transition to `closed` here. Keeping the
            # card in `cancelling` until that coroutine observes the request
            # prevents the UI from hiding a session that may still be created.
            return child
        try:
            await self._archive_child_upstream(child, session_key=session_key)
        except Exception:
            child.close_requested = False
            child.status = previous_status
            await self._emit()
            raise
        if previous_status not in TERMINAL_CHILD_STATES:
            child.status = "cancelled"
            child.ended_at = _now_iso()
        child.closed = True
        await self._emit()
        return child

    async def cancel_child(
        self, *, run_id: str, child_id: str, session_key: str
    ) -> MultiAgentChild:
        """Compatibility alias for clients built before CLOSE was introduced."""
        return await self.close_child(
            run_id=run_id, child_id=child_id, session_key=session_key
        )

    async def execute(
        self,
        *,
        plan_id: str,
        goal: str,
        steps: Sequence[dict[str, str]],
        session_key: str,
    ) -> MultiAgentRun:
        if not 1 <= len(steps) <= MAX_CHILDREN:
            raise ValueError(f"Parallel execution requires 1 to {MAX_CHILDREN} work steps.")
        async with self._lock:
            if self.active and self.active.status in {"starting", "running", "cancelling", "synthesizing"}:
                raise RuntimeError("A multi-agent run is already active.")
            run_id = uuid.uuid4().hex
            children = [
                MultiAgentChild(
                    id=str(step.get("id") or f"agent-{index + 1}"),
                    label=_bounded_text(step.get("title") or f"Agent {index + 1}", limit=120),
                    instruction=_bounded_text(step.get("instruction"), limit=20_000),
                )
                for index, step in enumerate(steps)
            ]
            self.active = MultiAgentRun(
                id=run_id,
                plan_id=plan_id,
                group_id=f"jarvis-plan-{run_id[:16]}",
                goal=_bounded_text(goal, limit=500),
                children=children,
            )
            self._cancel_requested = False
        await self._emit()

        for index, child in enumerate(tuple(self.active.children)):
            await self._spawn_child(child, index=index, session_key=session_key)

        self.active.status = self._aggregate_status()
        await self._emit()

        wait_started = asyncio.get_running_loop().time()
        while not self._cancel_requested:
            pending = {
                child.run_id: child
                for child in self.active.children
                if child.run_id and child.status in {"running", "cancelling"}
            }
            spawning = any(
                child.status in {"queued", "starting"}
                for child in self.active.children
            )
            if not pending:
                if spawning:
                    await asyncio.sleep(0.025)
                    continue
                break
            try:
                tasks = await self.gateway.list_tasks(session_key=session_key, limit=250)
            except Exception as exc:
                for child in pending.values():
                    if child.status not in TERMINAL_CHILD_STATES:
                        child.status = "failed"
                        child.error = _bounded_text(exc, limit=2_000)
                        child.ended_at = _now_iso()
                break
            by_run = {
                str(task.get("runId") or task.get("run_id") or ""): task
                for task in tasks if isinstance(task, dict)
            }
            for run_id, child in pending.items():
                task = by_run.get(run_id)
                if task is not None and not child.close_requested:
                    await self._apply_task_state(child, task, session_key=session_key)
            if asyncio.get_running_loop().time() - wait_started >= TASK_WAIT_SECONDS:
                for child in pending.values():
                    if child.status not in TERMINAL_CHILD_STATES:
                        child.status = "timed_out"
                        child.error = "Agent task did not reach a terminal state in time."
                        child.ended_at = _now_iso()
                await self._emit()
                break
            await self._emit()
            await asyncio.sleep(TASK_POLL_SECONDS)

        if self._cancel_requested:
            for child in self.active.children:
                if child.status not in TERMINAL_CHILD_STATES:
                    child.status = "cancelled"
                    child.ended_at = _now_iso()
        self.active.status = self._aggregate_status()
        await self._emit()
        return self.active

    def _aggregate_status(self) -> str:
        if self.active is None:
            return "idle"
        states = [child.status for child in self.active.children]
        if any(state not in TERMINAL_CHILD_STATES for state in states):
            return "running"
        succeeded = states.count("succeeded")
        if succeeded == len(states):
            return "synthesizing"
        if succeeded:
            return "partial"
        if states and all(state == "cancelled" for state in states):
            return "cancelled"
        return "failed"

    async def finish(self, *, status: str, summary: str = "", error: str = "") -> None:
        if self.active is None:
            return
        self.active.status = status
        self.active.summary = _bounded_text(summary)
        self.active.error = _bounded_text(error, limit=2_000)
        await self._emit()

    async def cancel(self, *, session_key: str) -> None:
        if self.active is None or self.active.status not in {"starting", "running", "synthesizing"}:
            return
        self._cancel_requested = True
        self.active.status = "cancelling"
        await self._emit()
        run_ids = {child.run_id for child in self.active.children if child.run_id}
        try:
            tasks = await self.gateway.list_tasks(session_key=session_key, statuses=["queued", "running"])
            for task in tasks:
                if str(task.get("runId") or task.get("run_id") or "") not in run_ids:
                    continue
                task_id = str(task.get("id") or task.get("taskId") or "")
                if task_id:
                    await self.gateway.cancel_task(task_id)
        finally:
            for child in self.active.children:
                if child.status not in TERMINAL_CHILD_STATES:
                    child.status = "cancelled"
                    child.ended_at = _now_iso()
            self.active.status = "cancelled"
            await self._emit()
