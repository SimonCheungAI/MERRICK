import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


sys.path.insert(0, Path(__file__).resolve().parents[1].joinpath("server").as_posix())

import harness_vault  # noqa: E402
import capability_catalog  # noqa: E402


class HarnessVaultTests(unittest.TestCase):
    def test_disabled_flag_returns_disabled_without_creating_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "PluginVault"
            with patch.dict(os.environ, {
                "JARVIS_HARNESS_MODE_V1": "false",
                "JARVIS_PLUGIN_VAULT_DIR": str(vault),
            }, clear=False):
                result = harness_vault.snapshot()

            self.assertEqual(result["status"], "disabled")
            self.assertFalse(result["available"])
            self.assertFalse(vault.exists())

    def test_enabled_flag_initializes_private_core_only_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "PluginVault"
            with patch.dict(os.environ, {
                "JARVIS_HARNESS_MODE_V1": "true",
                "JARVIS_PLUGIN_VAULT_DIR": str(vault),
            }, clear=False):
                result = harness_vault.snapshot()

            self.assertEqual(result["status"], "ready")
            self.assertTrue(result["available"])
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(result["active_generation"], 0)
            self.assertEqual(result["user_plugins"], 0)
            self.assertFalse(result["production_runtime"])
            self.assertTrue((vault / "registry.sqlite").is_file())
            self.assertEqual(vault.stat().st_mode & 0o777, 0o700)

    def test_safe_snapshot_fails_closed_when_vault_path_is_a_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            vault = root / "PluginVault"
            vault.symlink_to(target, target_is_directory=True)
            with patch.dict(os.environ, {
                "JARVIS_HARNESS_MODE_V1": "true",
                "JARVIS_PLUGIN_VAULT_DIR": str(vault),
            }, clear=False):
                result = harness_vault.safe_snapshot()

        self.assertFalse(result["available"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error_code"], "VAULT_UNAVAILABLE")
        self.assertFalse(result["production_runtime"])

    def test_safe_snapshot_rejects_a_symlinked_registry_database(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "PluginVault"
            vault.mkdir()
            redirected = root / "redirected.sqlite"
            redirected.touch()
            (vault / "registry.sqlite").symlink_to(redirected)
            with patch.dict(os.environ, {
                "JARVIS_HARNESS_MODE_V1": "true",
                "JARVIS_PLUGIN_VAULT_DIR": str(vault),
            }, clear=False):
                result = harness_vault.safe_snapshot()

            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(redirected.stat().st_size, 0)

    def test_capability_inventory_includes_read_only_harness_status(self):
        async def fake_cli(*args, **kwargs):
            if args[:2] == ("plugins", "list"):
                return '{"plugins": []}', ""
            return '{"skills": []}', ""

        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {
                "JARVIS_CAPABILITY_ADAPTER_V1": "true",
                "JARVIS_HARNESS_MODE_V1": "true",
                "JARVIS_PLUGIN_VAULT_DIR": str(Path(temporary) / "PluginVault"),
                "OPENCLAW_STATE_DIR": str(Path(temporary) / "OpenClaw"),
            }, clear=False):
                with patch.object(capability_catalog, "_cli", side_effect=fake_cli):
                    result = __import__("asyncio").run(capability_catalog.inventory())

        self.assertEqual(result["harness"]["status"], "ready")
        self.assertEqual(result["harness"]["active_generation"], 0)
        self.assertFalse(result["harness"]["production_runtime"])

    def test_capability_hud_shows_harness_readiness_behind_native_flag(self):
        root = Path(__file__).resolve().parents[1]
        frontend = (root / "web" / "app.js").read_text(encoding="utf-8")
        markup = (root / "web" / "index.html").read_text(encoding="utf-8")
        styles = (root / "web" / "style.css").read_text(encoding="utf-8")
        native = (root / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")

        self.assertIn('id="harness-mode-status"', markup)
        self.assertIn("renderHarnessStatus", frontend)
        self.assertIn("msg.harness", frontend)
        self.assertIn("width: min(920px, 100%)", styles)
        self.assertIn("font: 600 .8rem/1.5 var(--font-mono)", styles)
        self.assertIn('env["JARVIS_HARNESS_MODE_V1"] = "true"', native)

    def test_snapshot_closes_its_sqlite_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "PluginVault"
            vault.mkdir()
            (vault / "registry.sqlite").touch()
            connection = MagicMock()
            connection.__enter__.return_value = connection
            connection.execute.side_effect = lambda statement, *args: MagicMock(
                fetchone=lambda: (1,) if "schema_metadata" in statement else (0, 0)
            )
            with patch.dict(os.environ, {
                "JARVIS_HARNESS_MODE_V1": "true",
                "JARVIS_PLUGIN_VAULT_DIR": str(vault),
            }, clear=False), patch.object(harness_vault.sqlite3, "connect", return_value=connection):
                harness_vault.snapshot()

        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
