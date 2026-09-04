import asyncio
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from voice_turn_runtime import VoiceTurnRuntime  # noqa: E402


class VoiceTurnRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_external_clean_voice_edges_emit_one_start_per_turn(self) -> None:
        started: list[str] = []

        async def on_started() -> None:
            started.append("start")

        runtime = VoiceTurnRuntime(on_started)
        await runtime.start()
        try:
            await runtime.set_voice_activity(True)
            await runtime.set_voice_activity(True)  # duplicate native edge
            await runtime.set_voice_activity(False)
            await runtime.set_voice_activity(True)
            await runtime.set_voice_activity(False)
            self.assertEqual(started, ["start", "start"])
        finally:
            await runtime.close()
