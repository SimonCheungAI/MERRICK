import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path


sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parents[1].joinpath("server").as_posix())

import capability_catalog  # noqa: E402


PLUGIN_JSON = {
    "plugins": [
        {
            "id": "jarvis-safe-tools", "name": "MERRICK Safe Tools",
            "enabled": True, "status": "loaded", "origin": "config",
            "contracts": {"tools": ["jarvis_open_app"]},
            "dependencyStatus": {"requiredInstalled": True},
        },
        {
            "id": "workboard", "name": "Workboard", "description": "Track work.",
            "enabled": False, "status": "disabled", "origin": "bundled",
            "contracts": {"tools": ["workboard_list"]},
            "dependencyStatus": {"requiredInstalled": True},
        },
    ]
}
SKILL_JSON = {
    "skills": [
        {
            "name": "weather", "description": "Read weather.", "emoji": "☀️",
            "eligible": True, "disabled": False, "modelVisible": True,
            "source": "openclaw-bundled", "bundled": True, "missing": {},
        },
        {
            "name": "calendar", "description": "Use calendar.", "eligible": False,
            "disabled": True, "modelVisible": False, "source": "openclaw-bundled",
            "bundled": True, "missing": {"bins": ["calcli"]},
        },
    ]
}


class CapabilityCatalogTests(unittest.TestCase):
    def test_adapter_metadata_requires_an_explicit_true_feature_flag(self):
        async def run(flag, state_dir):
            with patch.dict(os.environ, {
                "JARVIS_CAPABILITY_ADAPTER_V1": flag,
                "OPENCLAW_STATE_DIR": state_dir,
            }, clear=False):
                with patch.object(
                    capability_catalog, "_cli",
                    AsyncMock(side_effect=[(json.dumps(PLUGIN_JSON), ""), (json.dumps(SKILL_JSON), "")]),
                ):
                    return await capability_catalog.inventory()

        with tempfile.TemporaryDirectory() as state_dir:
            disabled = asyncio.run(run("1", state_dir))
            enabled = asyncio.run(run("true", state_dir))
        self.assertNotIn("snapshot", disabled)
        self.assertNotIn("lifecycle", disabled["plugins"][0])
        self.assertIn("snapshot", enabled)
        self.assertIn("lifecycle", enabled["plugins"][0])

    def test_inventory_falls_back_to_a_versioned_last_safe_snapshot(self):
        async def run(state_dir):
            with patch.dict(os.environ, {
                "OPENCLAW_STATE_DIR": state_dir,
                "JARVIS_CAPABILITY_ADAPTER_V1": "true",
            }):
                with patch.object(
                    capability_catalog, "_cli",
                    AsyncMock(side_effect=[(json.dumps(PLUGIN_JSON), ""), (json.dumps(SKILL_JSON), "")]),
                ):
                    fresh = await capability_catalog.inventory()
                with patch.object(
                    capability_catalog, "_cli",
                    AsyncMock(side_effect=capability_catalog.CapabilityCatalogError("offline")),
                ):
                    stale = await capability_catalog.inventory()
                return fresh, stale

        with tempfile.TemporaryDirectory() as state_dir:
            fresh, stale = asyncio.run(run(state_dir))

        self.assertEqual(fresh["snapshot"]["schema_version"], 1)
        self.assertFalse(fresh["snapshot"]["stale"])
        self.assertEqual(stale["snapshot"]["schema_version"], 1)
        self.assertTrue(stale["snapshot"]["stale"])
        self.assertEqual(stale["summary"], fresh["summary"])
        self.assertEqual(stale["plugins"], fresh["plugins"])
        self.assertEqual(stale["skills"], fresh["skills"])

    def test_known_mail_and_calendar_candidates_have_conservative_profiles(self):
        gog = capability_catalog._skill_view({
            "name": "gog",
            "description": "Google Workspace CLI.",
            "eligible": False,
            "disabled": False,
            "modelVisible": False,
            "source": "openclaw-bundled",
            "bundled": True,
            "missing": {"bins": ["gog"]},
        })
        himalaya = capability_catalog._skill_view({
            "name": "himalaya",
            "description": "IMAP/SMTP mail CLI.",
            "eligible": False,
            "disabled": False,
            "modelVisible": False,
            "source": "openclaw-bundled",
            "bundled": True,
            "missing": {"bins": ["himalaya"]},
        })

        self.assertEqual(gog["execution_profile"]["candidate_domains"], ["mail", "calendar", "documents"])
        self.assertEqual(gog["execution_profile"]["max_risk"], "R2")
        self.assertFalse(gog["execution_profile"]["executable"])
        self.assertEqual(himalaya["execution_profile"]["candidate_domains"], ["mail"])
        self.assertEqual(himalaya["execution_profile"]["max_risk"], "R3")

    def test_plugin_compatibility_hash_changes_when_its_declared_tools_change(self):
        first = capability_catalog._plugin_view({
            "id": "mail-adapter",
            "enabled": True,
            "status": "loaded",
            "contracts": {"tools": ["mail_search"]},
            "dependencyStatus": {"requiredInstalled": True},
        })
        changed = capability_catalog._plugin_view({
            "id": "mail-adapter",
            "enabled": True,
            "status": "loaded",
            "contracts": {"tools": ["mail_search_v2"]},
            "dependencyStatus": {"requiredInstalled": True},
        })

        self.assertRegex(first["compatibility_hash"], r"^[a-f0-9]{64}$")
        self.assertNotEqual(first["compatibility_hash"], changed["compatibility_hash"])

    def test_capability_hud_renders_lifecycle_separately_from_toggle_state(self):
        root = Path(__file__).resolve().parents[1]
        frontend = (root / "web" / "app.js").read_text(encoding="utf-8")
        styles = (root / "web" / "style.css").read_text(encoding="utf-8")
        native = (root / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")

        self.assertIn("capability-lifecycle", frontend)
        self.assertIn("item.lifecycle", frontend)
        self.assertIn("capabilityLifecycleLabel", frontend)
        self.assertIn("item.execution_profile", frontend)
        self.assertIn("msg.snapshot", frontend)
        self.assertIn("capability_snapshot_stale", frontend)
        self.assertIn(".capability-lifecycle", styles)
        self.assertIn(".capability-risk", styles)
        self.assertIn('env["JARVIS_CAPABILITY_ADAPTER_V1"] = "true"', native)

    def test_inventory_separates_discovery_readiness_and_review_state(self):
        async def run(state_dir):
            with patch.dict(os.environ, {
                "JARVIS_CAPABILITY_ADAPTER_V1": "true",
                "OPENCLAW_STATE_DIR": state_dir,
            }):
                with patch.object(
                    capability_catalog, "_cli",
                    AsyncMock(side_effect=[(json.dumps(PLUGIN_JSON), ""), (json.dumps(SKILL_JSON), "")]),
                ):
                    return await capability_catalog.inventory()

        with tempfile.TemporaryDirectory() as state_dir:
            result = asyncio.run(run(state_dir))
        core = next(item for item in result["plugins"] if item["id"] == "jarvis-safe-tools")
        self.assertEqual(core["lifecycle"], {
            "discovery": "discovered",
            "enablement": "enabled",
            "readiness": "ready",
            "review": "core",
            "connection": "not_assessed",
            "authorization": "policy_managed",
        })
        workboard = next(item for item in result["plugins"] if item["id"] == "workboard")
        self.assertEqual(workboard["lifecycle"]["readiness"], "disabled")
        self.assertEqual(workboard["lifecycle"]["review"], "unreviewed")
        weather = next(item for item in result["skills"] if item["id"] == "weather")
        self.assertEqual(weather["lifecycle"]["readiness"], "ready")
        self.assertEqual(weather["lifecycle"]["review"], "unreviewed")
        calendar = next(item for item in result["skills"] if item["id"] == "calendar")
        self.assertEqual(calendar["lifecycle"]["readiness"], "dependency_missing")
        self.assertEqual(calendar["lifecycle"]["authorization"], "not_assessed")

    def test_inventory_normalizes_and_locks_core_plugin(self):
        async def run():
            with patch.object(
                capability_catalog, "_cli",
                AsyncMock(side_effect=[(json.dumps(PLUGIN_JSON), ""), (json.dumps(SKILL_JSON), "")]),
            ):
                return await capability_catalog.inventory()

        result = asyncio.run(run())
        self.assertEqual(result["summary"], {
            "plugins_total": 2, "plugins_enabled": 1,
            "skills_total": 2, "skills_ready": 1,
        })
        core = next(item for item in result["plugins"] if item["id"] == "jarvis-safe-tools")
        self.assertTrue(core["locked"])
        self.assertEqual(core["surfaces"], ["jarvis_open_app"])
        disabled = next(item for item in result["skills"] if item["id"] == "calendar")
        self.assertFalse(disabled["enabled"])
        self.assertEqual(disabled["requirements"], ["calcli"])

    def test_plugin_toggle_rejects_core_and_invalid_identifiers(self):
        async def run():
            with self.assertRaises(capability_catalog.CapabilityCatalogError):
                await capability_catalog.set_plugin_enabled("jarvis-safe-tools", False)
            with self.assertRaises(capability_catalog.CapabilityCatalogError):
                await capability_catalog.set_plugin_enabled("bad; id", True)
        asyncio.run(run())

    def test_skill_toggle_uses_only_boolean_config_setting(self):
        async def run():
            with patch.object(capability_catalog, "_cli", AsyncMock(return_value=("", ""))) as cli:
                await capability_catalog.set_skill_enabled("weather", False)
            cli.assert_awaited_once_with(
                "config", "set", "skills.entries.weather.enabled", "false", "--strict-json", timeout=35.0,
            )
        asyncio.run(run())

    def test_plugin_toggle_uses_official_enable_disable_command(self):
        async def run():
            with patch.object(capability_catalog, "_cli", AsyncMock(return_value=("", ""))) as cli:
                await capability_catalog.set_plugin_enabled("workboard", True)
            cli.assert_awaited_once_with("plugins", "enable", "workboard", timeout=35.0)
        asyncio.run(run())

    def test_gateway_plugin_review_keeps_token_out_of_public_payload(self):
        async def run():
            request = AsyncMock(return_value={
                "ok": True,
                "plugin": {
                    "id": "workboard", "name": "Workboard", "installed": True,
                    "enabled": False, "description": "Track delegated work.",
                },
                "declared": {"tools": ["workboard_list", "workboard_create"], "channels": []},
                "reviewToken": "server-held-review-token",
                "trust": {"disposition": "clean"},
            })
            prepared = await capability_catalog.prepare_gateway_change(
                "plugin", "workboard", True, request,
            )
            return request, prepared

        request, prepared = asyncio.run(run())
        request.assert_awaited_once_with("plugins.inspect", {"pluginId": "workboard"})
        self.assertNotIn("review_token", prepared["public"])
        self.assertEqual(prepared["review_token"], "server-held-review-token")
        self.assertEqual(prepared["public"]["surfaces"][0]["count"], 2)
        self.assertEqual(prepared["public"]["trust"], "clean")

    def test_gateway_plugin_change_uses_reviewed_openclaw_rpc(self):
        async def run():
            request = AsyncMock(return_value={"ok": True, "restartRequired": True})
            restarted = await capability_catalog.apply_gateway_change({
                "public": {"kind": "plugin", "id": "workboard", "enabled": True},
                "review_token": "review-token",
            }, request)
            return request, restarted

        request, restarted = asyncio.run(run())
        request.assert_awaited_once_with("plugins.setEnabled", {
            "pluginId": "workboard",
            "enabled": True,
            "acknowledgeCapabilities": {"reviewToken": "review-token"},
        })
        self.assertTrue(restarted)

    def test_gateway_skill_change_is_verified_then_updated(self):
        async def run():
            request = AsyncMock(side_effect=[{
                "skills": [{
                    "skillKey": "weather", "name": "weather", "description": "Read weather.",
                    "missing": {"bins": [], "env": []},
                }],
            }, {"ok": True}])
            prepared = await capability_catalog.prepare_gateway_change(
                "skill", "weather", False, request,
            )
            restarted = await capability_catalog.apply_gateway_change(prepared, request)
            return request, prepared, restarted

        request, prepared, restarted = asyncio.run(run())
        self.assertEqual(request.await_args_list[0].args, ("skills.status", {"agentId": "main"}))
        self.assertEqual(request.await_args_list[1].args, ("skills.update", {"skillKey": "weather", "enabled": False}))
        self.assertEqual(prepared["public"]["trust"], "installed-skill")
        self.assertFalse(restarted)

    def test_discover_plugins_uses_gateway_catalog_and_clawhub_search(self):
        async def run():
            request = AsyncMock(side_effect=[{
                "mutationAllowed": True,
                "plugins": [{
                    "id": "diffs", "name": "Diffs", "description": "Read-only diff viewer.",
                    "version": "2026.8.1", "featured": True, "installed": False,
                    "enabled": False, "removable": False,
                    "install": {"source": "official", "pluginId": "diffs"},
                }],
            }, {
                "results": [{
                    "score": 1,
                    "package": {
                        "name": "@community/calendar", "displayName": "Calendar",
                        "family": "code-plugin", "channel": "community", "isOfficial": False,
                        "summary": "Calendar tools.", "latestVersion": "1.2.0",
                        "runtimeId": "calendar", "downloads": 42,
                    },
                }],
            }])
            payload = await capability_catalog.discover_plugins(request, "calendar")
            return request, payload

        request, payload = asyncio.run(run())
        self.assertTrue(payload["mutation_allowed"])
        self.assertEqual(payload["catalog"][0]["install_identity"], "@community/calendar")
        self.assertFalse(payload["catalog"][0]["official"])
        self.assertEqual(request.await_args_list[0].args, ("plugins.list", {}))
        self.assertEqual(request.await_args_list[1].args, ("plugins.search", {"query": "calendar", "limit": 24}))

    def test_prepare_install_accepts_only_current_openclaw_catalog_entry(self):
        async def run():
            request = AsyncMock(return_value={
                "mutationAllowed": True,
                "plugins": [{
                    "id": "diffs", "name": "Diffs", "description": "Read-only diff viewer.",
                    "version": "2026.8.1", "installed": False,
                    "install": {"source": "official", "pluginId": "diffs"},
                }],
            })
            prepared = await capability_catalog.prepare_plugin_operation(
                "install", "diffs", "official", request,
            )
            return prepared

        prepared = asyncio.run(run())
        self.assertEqual(prepared["request"], {"source": "official", "pluginId": "diffs"})
        self.assertEqual(prepared["public"]["stage"], "identity")
        self.assertNotIn("review_token", prepared["public"])

    def test_install_capability_consent_is_returned_for_review_without_leaking_token(self):
        async def run():
            request = AsyncMock(side_effect=[
                capability_catalog.OpenClawGatewayRPCError(
                    'Plugin "diffs" requires capability consent.',
                    details={
                        "capabilityConsentCode": "PLUGIN_CAPABILITY_CONSENT_REQUIRED",
                        "pluginId": "diffs",
                        "reviewToken": "server-only-review-token",
                        "widened": {"tools": ["diffs"]},
                    },
                ),
                {
                    "ok": True,
                    "plugin": {"id": "diffs", "name": "Diffs", "description": "Read-only diff viewer."},
                    "source": {"kind": "clawhub", "packageName": "@openclaw/diffs", "integrity": "sha256-test", "integrityKind": "sha256"},
                    "declared": {"tools": ["diffs"]},
                    "grants": {"hooks": {
                        "allowPromptInjection": {"effective": True},
                        "allowConversationAccess": {"effective": False},
                    }},
                    "trust": {"disposition": "clean"},
                },
            ])
            prepared = {
                "public": {"action": "install", "name": "Diffs", "stage": "identity"},
                "request": {"source": "official", "pluginId": "diffs"},
            }
            return await capability_catalog.apply_plugin_operation(prepared, request)

        outcome = asyncio.run(run())
        self.assertEqual(outcome["status"], "review")
        self.assertEqual(outcome["prepared"]["review_token"], "server-only-review-token")
        self.assertNotIn("review_token", outcome["prepared"]["public"])
        self.assertEqual(outcome["prepared"]["public"]["source_info"]["integrity"], "sha256-test")
        self.assertTrue(outcome["prepared"]["public"]["grants"][0]["effective"])

    def test_confirmed_install_sends_server_held_review_token(self):
        async def run():
            request = AsyncMock(return_value={
                "ok": True, "restartRequired": True,
                "plugin": {"id": "diffs", "name": "Diffs"},
            })
            outcome = await capability_catalog.apply_plugin_operation({
                "public": {"action": "install", "name": "Diffs", "stage": "capabilities"},
                "request": {"source": "official", "pluginId": "diffs"},
                "review_token": "server-only-review-token",
            }, request)
            return request, outcome

        request, outcome = asyncio.run(run())
        request.assert_awaited_once_with("plugins.install", {
            "source": "official", "pluginId": "diffs",
            "acknowledgeCapabilities": {"reviewToken": "server-only-review-token"},
        })
        self.assertEqual(outcome["status"], "changed")
        self.assertTrue(outcome["restart_required"])

    def test_diagnostics_keeps_warning_findings_from_nonzero_lint(self):
        async def run():
            with patch.object(
                capability_catalog, "_cli",
                AsyncMock(return_value=(json.dumps({"ok": False, "findings": [
                    {"severity": "warning", "message": "Missing local dependency."}
                ]}), "")),
            ) as cli:
                result = await capability_catalog.diagnostics()
            cli.assert_awaited_once_with(
                "doctor", "--lint", "--json", "--non-interactive",
                timeout=50.0, allow_nonzero=True,
            )
            return result
        self.assertEqual(asyncio.run(run()), [{"severity": "warning", "message": "Missing local dependency."}])

    def test_diagnostics_accepts_a_cli_notice_before_the_json_envelope(self):
        async def run():
            output = "OpenClaw loaded local providers.\n" + json.dumps({
                "ok": False,
                "findings": [{"severity": "warning", "message": "Missing local dependency."}],
            })
            with patch.object(
                capability_catalog,
                "_cli",
                AsyncMock(return_value=(output, "")),
            ):
                return await capability_catalog.diagnostics()

        self.assertEqual(
            asyncio.run(run()),
            [{"severity": "warning", "message": "Missing local dependency."}],
        )


if __name__ == "__main__":
    unittest.main()
