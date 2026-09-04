"""Persistent adapter around OpenClaw's official Gateway WebSocket client."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


# OpenClaw task/session/history snapshots can legitimately exceed asyncio's
# 64 KiB StreamReader default. A larger bounded reader keeps one JSON frame
# intact instead of disconnecting the shared Gateway client mid-request.
GATEWAY_FRAME_LIMIT = 8 * 1024 * 1024


class OpenClawGatewayRPCError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "GATEWAY_REQUEST_FAILED",
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class OpenClawGatewayRPC:
    def __init__(self, *, project_root: Path, node_path: Path) -> None:
        self.project_root = project_root
        self.node_path = node_path
        self.bridge_path = project_root / "openclaw/gateway-client-bridge/index.mjs"
        self.process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._ready: asyncio.Future | None = None
        self._pending: dict[str, asyncio.Future] = {}
        self._events: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=512)
        self._event_subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._start_lock = asyncio.Lock()

    async def start(self, *, url: str, token: str) -> None:
        async with self._start_lock:
            if self.process is not None and self.process.returncode is None:
                return
            if not self.node_path.is_file() or not self.bridge_path.is_file():
                raise OpenClawGatewayRPCError("The official OpenClaw Gateway client is unavailable.")
            loop = asyncio.get_running_loop()
            self._ready = loop.create_future()
            environment = os.environ.copy()
            environment["OPENCLAW_GATEWAY_URL"] = url
            environment["OPENCLAW_GATEWAY_TOKEN"] = token
            self.process = await asyncio.create_subprocess_exec(
                str(self.node_path),
                str(self.bridge_path),
                cwd=str(self.project_root),
                env=environment,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                limit=GATEWAY_FRAME_LIMIT,
            )
            self._reader_task = asyncio.create_task(self._read_frames())
        try:
            await asyncio.wait_for(asyncio.shield(self._ready), timeout=15.0)
        except Exception as exc:
            await self.stop()
            raise OpenClawGatewayRPCError("The official OpenClaw Gateway client did not connect.") from exc

    async def _read_frames(self) -> None:
        process = self.process
        if process is None or process.stdout is None:
            return
        try:
            while line := await process.stdout.readline():
                try:
                    frame = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                frame_type = frame.get("type")
                if frame_type == "ready":
                    if self._ready is not None and not self._ready.done():
                        self._ready.set_result(frame)
                elif frame_type == "response":
                    request_id = frame.get("id")
                    future = self._pending.pop(request_id, None)
                    if future is not None and not future.done():
                        if frame.get("ok") is True:
                            future.set_result(frame.get("result"))
                        else:
                            error = frame.get("error") or {}
                            future.set_exception(
                                OpenClawGatewayRPCError(
                                    str(error.get("message") or "The OpenClaw request failed."),
                                    code=str(error.get("code") or "GATEWAY_REQUEST_FAILED"),
                                    details=error.get("details"),
                                )
                            )
                elif frame_type == "event":
                    if self._events.full():
                        self._events.get_nowait()
                    self._events.put_nowait(frame)
                    for subscriber in tuple(self._event_subscribers):
                        if subscriber.full():
                            subscriber.get_nowait()
                        subscriber.put_nowait(frame)
                elif frame_type in {"fatal", "connection_error"}:
                    message = str(frame.get("message") or "The OpenClaw Gateway connection failed.")
                    error = OpenClawGatewayRPCError(message)
                    if self._ready is not None and not self._ready.done():
                        self._ready.set_exception(error)
                    self._fail_pending(error)
        finally:
            error = OpenClawGatewayRPCError("The OpenClaw Gateway client disconnected.")
            if self._ready is not None and not self._ready.done():
                self._ready.set_exception(error)
            self._fail_pending(error)

    def _fail_pending(self, error: Exception) -> None:
        pending, self._pending = self._pending, {}
        for future in pending.values():
            if not future.done():
                future.set_exception(error)

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> Any:
        process = self.process
        if process is None or process.returncode is not None or process.stdin is None:
            raise OpenClawGatewayRPCError("The OpenClaw Gateway client is not connected.")
        request_id = secrets.token_hex(16)
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        frame = json.dumps(
            {"id": request_id, "method": method, "params": params or {}},
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        try:
            process.stdin.write(frame)
            await process.stdin.drain()
            return await asyncio.wait_for(future, timeout=timeout)
        except Exception:
            self._pending.pop(request_id, None)
            if not future.done():
                future.cancel()
            raise

    async def next_event(self, *, timeout: float | None = None) -> dict[str, Any]:
        if timeout is None:
            return await self._events.get()
        return await asyncio.wait_for(self._events.get(), timeout=timeout)

    @asynccontextmanager
    async def event_subscription(
        self,
        *,
        maxsize: int = 256,
    ) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        """Fan out live events without allowing consumers to steal them."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=maxsize)
        self._event_subscribers.add(queue)
        try:
            yield queue
        finally:
            self._event_subscribers.discard(queue)

    async def stop(self) -> None:
        process, self.process = self.process, None
        if process is not None and process.returncode is None:
            if process.stdin is not None:
                try:
                    process.stdin.write(b'{"type":"shutdown"}\n')
                    await process.stdin.drain()
                    process.stdin.close()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
        reader, self._reader_task = self._reader_task, None
        if reader is not None and reader is not asyncio.current_task() and not reader.done():
            reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)
        self._fail_pending(OpenClawGatewayRPCError("The OpenClaw Gateway client stopped."))
