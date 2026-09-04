"""Regression coverage for the persistent OpenClaw Gateway transport."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from openclaw_gateway_rpc import GATEWAY_FRAME_LIMIT, OpenClawGatewayRPC  # noqa: E402


class _Stdout:
    def __init__(self) -> None:
        self.sent_ready = False
        self.block = asyncio.Event()

    async def readline(self) -> bytes:
        if not self.sent_ready:
            self.sent_ready = True
            return b'{"type":"ready"}\n'
        await self.block.wait()
        return b""


class _Stdin:
    def write(self, _data: bytes) -> None:
        return None

    async def drain(self) -> None:
        return None

    def close(self) -> None:
        return None


class _Process:
    def __init__(self) -> None:
        self.returncode = None
        self.stdout = _Stdout()
        self.stdin = _Stdin()

    async def wait(self) -> int:
        self.returncode = 0
        return 0

    def terminate(self) -> None:
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9


class GatewayRPCTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_bridge_stream_accepts_multi_megabyte_json_frames(self) -> None:
        process = _Process()
        rpc = OpenClawGatewayRPC(
            project_root=PROJECT_ROOT,
            node_path=Path("/usr/bin/true"),
        )

        with patch(
            "openclaw_gateway_rpc.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ) as launch:
            await rpc.start(url="ws://127.0.0.1:18789", token="a" * 64)
            self.assertEqual(launch.await_args.kwargs["limit"], GATEWAY_FRAME_LIMIT)
            self.assertGreater(GATEWAY_FRAME_LIMIT, 64 * 1024)
            await rpc.stop()


if __name__ == "__main__":
    unittest.main()
