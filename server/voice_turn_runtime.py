"""Small Pipecat-backed bridge for native barge-in signals.

The macOS host owns the actual acoustic capture and echo suppression.  This
module deliberately does not add a second microphone or VAD implementation:
it translates the host's confirmed clean-speech edges into Pipecat's tested
turn lifecycle so cancellation has one owner in the backend.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from pipecat.frames.frames import UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.turns.user_start import ExternalUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_controller import UserTurnController
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.utils.asyncio.task_manager import TaskManager


class VoiceTurnRuntime:
    """Own the clean-speech start/stop state for one WebSocket session."""

    def __init__(self, on_user_started: Callable[[], Awaitable[None]]):
        self._on_user_started = on_user_started
        self._task_manager: TaskManager | None = None
        # We need explicitly emitted edges: macOS already has the AEC signal,
        # and adding Pipecat's own microphone VAD would capture a second stream.
        self._controller = UserTurnController(
            user_turn_strategies=UserTurnStrategies(
                start=[ExternalUserTurnStartStrategy()],
                stop=[ExternalUserTurnStopStrategy(wait_for_transcript=False)],
            ),
            user_turn_stop_timeout=2.0,
        )
        self._active = False

        @self._controller.event_handler("on_user_turn_started")
        async def _on_started(_controller, _strategy, _params):
            await self._on_user_started()

    async def start(self) -> None:
        self._task_manager = TaskManager()
        await self._controller.setup(self._task_manager)

    async def set_voice_activity(self, active: bool) -> None:
        if active == self._active:
            return
        self._active = active
        if active:
            await self._controller.process_frame(UserStartedSpeakingFrame())
        else:
            await self._controller.process_frame(UserStoppedSpeakingFrame())

    async def close(self) -> None:
        self._active = False
        await self._controller.cleanup()
