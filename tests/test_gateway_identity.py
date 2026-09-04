import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from openclaw_client import OpenClawError, OpenClawGateway  # noqa: E402


class GatewayIdentityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gateway = OpenClawGateway()
        self.gateway.config_path = Path(self.temp_dir.name) / "openclaw.json"
        self.gateway.owner_path = Path(self.temp_dir.name) / ".gateway-owner.json"

    async def asyncTearDown(self) -> None:
        self.temp_dir.cleanup()

    def expected_open_files(self, pid: int, *, project_root: Path = PROJECT_ROOT) -> str:
        return "\n".join(
            (
                f"p{pid}",
                "fcwd",
                f"n{project_root.resolve()}",
                "ftxt",
                f"n{self.gateway._expected_node_path()}",
                "f22",
                f"n{self.gateway.config_path.resolve()}",
            )
        )

    async def test_accepts_the_owned_runtime_after_process_title_changes(self) -> None:
        pid = 4242
        self.gateway._command_output = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                (0, f"{os.getuid()} openclaw\n"),
                (0, self.expected_open_files(pid)),
            ]
        )
        self.assertTrue(await self.gateway._process_fingerprint_matches(pid))

    async def test_rejects_a_same_named_process_with_the_wrong_project(self) -> None:
        pid = 4243
        self.gateway._command_output = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                (0, f"{os.getuid()} openclaw\n"),
                (0, self.expected_open_files(pid, project_root=Path("/tmp/not-jarvis"))),
            ]
        )
        self.assertFalse(await self.gateway._process_fingerprint_matches(pid))

    async def test_secondary_client_shutdown_preserves_live_owner_record(self) -> None:
        self.gateway.owner_path.write_text(
            '{"pid":4244,"port":23456}', encoding="utf-8"
        )
        self.gateway.process = None

        await self.gateway.shutdown()

        self.assertTrue(self.gateway.owner_path.is_file())

    async def test_failed_previous_owner_termination_preserves_live_owner_record(self) -> None:
        self.gateway.owner_path.write_text(
            '{"pid":4247,"port":23457}', encoding="utf-8"
        )
        self.gateway._terminate_verified_gateway = AsyncMock(  # type: ignore[method-assign]
            return_value=False
        )
        self.gateway._managed_gateway_processes = AsyncMock(  # type: ignore[method-assign]
            return_value=[4247]
        )
        self.gateway._process_parent_pid = AsyncMock(  # type: ignore[method-assign]
            return_value=777
        )

        with self.assertRaises(OpenClawError):
            await self.gateway._clean_previous_owner()

        self.assertTrue(self.gateway.owner_path.is_file())

    async def test_successful_previous_owner_termination_removes_owner_record(self) -> None:
        self.gateway.owner_path.write_text(
            '{"pid":4249,"port":23459}', encoding="utf-8"
        )
        self.gateway._terminate_verified_gateway = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )
        self.gateway._managed_gateway_processes = AsyncMock(  # type: ignore[method-assign]
            return_value=[]
        )
        self.gateway._legacy_orphaned_gateway_processes = AsyncMock(  # type: ignore[method-assign]
            return_value=[]
        )

        await self.gateway._clean_previous_owner()

        self.assertFalse(self.gateway.owner_path.exists())

    async def test_missing_owner_record_is_restored_for_live_owned_gateway(self) -> None:
        self.gateway.process = unittest.mock.Mock(pid=4248, returncode=None)
        self.gateway.port = 23458
        self.gateway._process_owns_listener = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )
        self.gateway._authenticated_ready = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )

        restored = await self.gateway.repair_owner_record_if_owned()

        self.assertTrue(restored)
        self.assertEqual(
            self.gateway.owner_path.read_text(encoding="utf-8"),
            '{"pid":4248,"port":23458}',
        )

    async def test_owner_repair_does_not_overwrite_an_existing_receipt(self) -> None:
        self.gateway.owner_path.write_text(
            '{"pid":4250,"port":23460}', encoding="utf-8"
        )
        self.gateway.process = unittest.mock.Mock(pid=4251, returncode=None)
        self.gateway.port = 23461

        restored = await self.gateway.repair_owner_record_if_owned()

        self.assertFalse(restored)
        self.assertEqual(
            self.gateway.owner_path.read_text(encoding="utf-8"),
            '{"pid":4250,"port":23460}',
        )

    async def test_recovers_only_a_parentless_verified_gateway_without_an_owner_record(self) -> None:
        self.gateway._managed_gateway_processes = AsyncMock(  # type: ignore[method-assign]
            side_effect=[[4245], []]
        )
        self.gateway._process_parent_pid = AsyncMock(return_value=1)  # type: ignore[method-assign]
        self.gateway._terminate_verified_gateway = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await self.gateway._clean_previous_owner()

        self.gateway._terminate_verified_gateway.assert_awaited_once_with(4245)

    async def test_never_reclaims_a_verified_gateway_attached_to_another_parent(self) -> None:
        self.gateway._managed_gateway_processes = AsyncMock(return_value=[4246])  # type: ignore[method-assign]
        self.gateway._process_parent_pid = AsyncMock(return_value=777)  # type: ignore[method-assign]
        self.gateway._terminate_verified_gateway = AsyncMock()  # type: ignore[method-assign]

        with self.assertRaises(OpenClawError):
            await self.gateway._clean_previous_owner()

        self.gateway._terminate_verified_gateway.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
