from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))
from main import workspace_control_intent  # noqa: E402
from openclaw_client import OpenClawGateway  # noqa: E402


class DesktopLifecycleTests(unittest.TestCase):
    def test_release_preflight_enforces_provider_binding_contract(self) -> None:
        verifier = PROJECT_ROOT / "scripts" / "verify-provider-bindings.py"
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(
            encoding="utf-8"
        )

        self.assertTrue(verifier.is_file())
        self.assertIn('verify-provider-bindings.py" "$ROOT"', build)
        completed = subprocess.run(
            [sys.executable, str(verifier), str(PROJECT_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Runtime connection contract verified", completed.stdout)

    def test_provider_defaults_use_current_official_model_ids(self) -> None:
        contract = (PROJECT_ROOT / "config" / "runtime-contract.json").read_text(
            encoding="utf-8"
        )

        for model_id in (
            'model: "gpt-5.5"',
            'model: "claude-sonnet-5"',
            'model: "gemini-3.1-pro-preview"',
            'model: "kimi-k3"',
            'model: "deepseek-v4-pro"',
        ):
            self.assertIn(model_id.removeprefix('model: '), contract)
        for retired_or_invalid in (
            'model: "claude-sonnet-4-7"',
            'model: "kimi-k2.6"',
            'model: "deepseek-chat"',
        ):
            self.assertNotIn(retired_or_invalid.removeprefix('model: '), contract)

    def test_desktop_is_discoverable_from_the_dock_and_application_switcher(self) -> None:
        plist = (PROJECT_ROOT / "desktop" / "Info.plist").read_text(encoding="utf-8")
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("<key>LSUIElement</key><true/>", plist)
        self.assertIn("app.setActivationPolicy(.regular)", source)

    def test_second_bundle_copy_redirects_to_the_existing_instance_before_backend_start(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("redirectToExistingInstanceIfNeeded", source)
        redirect = source[
            source.index("private func redirectToExistingInstanceIfNeeded"):
            source.index("private func rememberFrontmostApplication")
        ]
        self.assertIn("NSRunningApplication", redirect)
        self.assertIn("runningApplications(withBundleIdentifier:", redirect)
        self.assertIn("app.duplicate_launch_redirected", source)

        launch = source[source.index("func applicationDidFinishLaunching"):source.index("private func rememberFrontmostApplication")]
        self.assertIn("if redirectToExistingInstanceIfNeeded()", launch)
        self.assertLess(
            launch.index("redirectToExistingInstanceIfNeeded()"),
            launch.index("buildWindow()"),
        )
        self.assertLess(
            launch.index("redirectToExistingInstanceIfNeeded()"),
            launch.index("startBackend()"),
        )

    def test_reopening_from_the_dock_brings_the_hud_to_the_primary_screen(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("bringHUDToPrimaryScreen", source)
        reopen = source[
            source.index("func applicationShouldHandleReopen"):
            source.index("func applicationDidBecomeActive")
        ]
        self.assertIn("bringHUDToPrimaryScreen()", reopen)
        self.assertIn("NSScreen.main", source)

    def test_global_jarvis_identity_does_not_depend_on_owner_voice_verification(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn("GLOBAL_MERRICK_IDENTITY_PROMPT", source)
        self.assertIn("independently of speaker verification", source)
        self.assertIn("never ask who you are", source)

    def test_app_bootstrap_refreshes_global_identity_in_every_openclaw_workspace(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        bootstrap = (PROJECT_ROOT / "scripts" / "setup-openclaw.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("synchronizeOpenClawWorkspaceIdentity()", native)
        self.assertIn("openclaw.global_identity_refreshed", native)
        for workspace in ("workspace", "action-planner-workspace"):
            for filename in ("IDENTITY.md", "SOUL.md"):
                path = PROJECT_ROOT / "openclaw" / workspace / filename
                self.assertTrue(path.is_file(), path)
                self.assertIn("MERRICK", path.read_text(encoding="utf-8"))
                self.assertIn(
                    f"openclaw/{workspace}/{filename}", bootstrap
                )

    def test_generated_gateway_config_keeps_openclaw_write_metadata_after_oauth(self) -> None:
        config = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn('lastTouchedVersion: "2026.8.1"', config)
        self.assertNotIn("lastTouchedAt", config)
        self.assertIn("synchronizeProviderGatewayTemplate()", native)

    def test_source_setup_stages_the_pinned_codex_provider_as_bundled(self) -> None:
        source = (PROJECT_ROOT / "scripts" / "setup-openclaw.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('node_modules/@openclaw/codex', source)
        self.assertIn('node_modules/openclaw/dist/extensions/codex', source)
        self.assertIn('/usr/bin/ditto "$CODEX_PROVIDER_PACKAGE" "$BUNDLED_CODEX_DIR"', source)

    def test_codex_connection_is_usable_only_after_app_owned_oauth_reaches_the_runtime(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        login = native[
            native.index("private func startMerrickCodexDeviceConnection"):
            native.index("private func cancelProviderConnection")
        ]
        status = native[
            native.index("private func providerStatePayload"):
            native.index("private func jsObject")
        ]

        self.assertIn('process.executableURL = URL(fileURLWithPath: "/usr/bin/script")', login)
        self.assertIn('"-q", "/dev/null", cli.node.path, cli.entry.path', login)
        self.assertIn('"models", "auth", "--agent", "main", "login"', login)
        self.assertNotIn('"--force"', login)
        self.assertNotIn("Your previous connection was kept", login)
        self.assertIn("providerConnectionIsUsable(profile)", status)
        self.assertIn('"configured": usable', status)
        self.assertIn("hasExistingOpenClawUserState()", status)
        self.assertIn('"provider": effectiveProfile.provider', status)
        self.assertIn('"model": effectiveProfile.model', status)
        self.assertIn('"onboardingRequired": onboardingRequired', status)

    def test_provider_manager_displays_the_effective_model_connection_state(self) -> None:
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn('id="provider-connection-summary"', html)
        self.assertIn('const providerConnectionSummary = $("provider-connection-summary")', web)
        display = web[
            web.index("function displayProviderConnection"):
            web.index("function applyProviderConnectionState")
        ]
        self.assertIn("providerConnectionSummary", display)
        self.assertIn("state?.model", display)
        self.assertIn('"type": "model_runtime_status"', backend)
        self.assertIn('case "model_runtime_status"', web)
        self.assertIn("providerRuntimeState", display)

    def test_backend_always_receives_the_effective_default_provider_environment(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        environment = native[
            native.index("private func applyProviderEnvironment"):
            native.index("private func merrickOpenClawEnvironment")
        ]

        self.assertIn('environment["JARVIS_PROJECT_ROOT"] = projectRoot.path', environment)
        self.assertIn("readProviderProfile() ?? ProviderProfile(", environment)
        self.assertNotIn("guard let profile = readProviderProfile() else { return }", environment)
        self.assertIn(
            "configureProviderEnvironment(&environment, profile: profile, apiKey: apiKey)",
            environment,
        )
        self.assertIn('environment["JARVIS_MODEL_API_KEY"] = apiKey ?? "unused"', native)

    def test_failed_provider_setup_refreshes_the_visible_connection_state(self) -> None:
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        handler = web[
            web.index("window.merrickNativeProviderSetupResult"):
            web.index("window.merrickNativeProviderSetupProgress")
        ]

        self.assertIn("applyProviderConnectionState(result, {preserveDraft: true})", handler)
        self.assertLess(
            handler.index("applyProviderConnectionState(result, {preserveDraft: true})"),
            handler.index("if (!ok) return"),
        )
        self.assertLess(handler.index("applyProviderConnectionState(result,"), handler.index("setProviderSetupStatus(message,"))
        self.assertLess(handler.index("providerDeviceCode.hidden = true"), handler.index("if (!ok) return"))
        self.assertLess(handler.index("providerCancelBtn.hidden = true"), handler.index("if (!ok) return"))

    def test_model_switch_reuses_credentials_only_for_the_same_endpoint(self) -> None:
        source = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        handler = source[source.index("private func saveProviderAPIKey"):source.index("private func finishProviderOnboarding")]
        self.assertIn('body["reuseSavedKey"] as? Bool == true', handler)
        self.assertIn("current.provider == provider, current.baseURL == baseURL", handler)
        self.assertLess(handler.index("current.baseURL == baseURL"), handler.index("providerCredential(for: provider)"))

    def test_reopening_settings_replays_the_pending_login_code_and_model(self) -> None:
        source = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        self.assertIn('payload["model"] = pending.model', source)
        state = source[source.index("private func sendProviderSetupState"):source.index("private func markProviderConnectionFailed")]
        self.assertIn("providerLoginProcess?.isRunning == true", state)
        self.assertIn("deviceCode: providerPresentedDeviceCode", state)

    def test_provider_login_parser_extracts_code_from_ansi_terminal_output(self) -> None:
        parser = PROJECT_ROOT / "desktop" / "ProviderLoginParser.swift"
        with tempfile.TemporaryDirectory() as directory:
            harness = Path(directory) / "ProviderLoginParserHarness.swift"
            executable = Path(directory) / "provider-login-parser-test"
            harness.write_text(
                r'''
import Foundation

@main
struct ProviderLoginParserHarness {
    static func main() {
        let raw = "\u{001B}[?25lJARVIS-COMPATIBLE https://docs.openclaw.ai/start/faq\r\n\u{001B}[2K│ URL: https://auth.openai.com/codex/device\u{001B}[0m\r\n│ Code: ABCD\u{001B}[36m-EFGH\u{001B}[0m\r\n"
        let prompt = ProviderLoginParser.parse(raw)
        precondition(prompt.verificationURL?.absoluteString == "https://auth.openai.com/codex/device")
        precondition(prompt.deviceCode == "ABCD-EFGH")
        // Codes are opaque: don't change the provider's casing or require a separator.
        precondition(ProviderLoginParser.parse("Code: aBcD-eFgH1\n").deviceCode == "aBcD-eFgH1")
        precondition(ProviderLoginParser.parse("Code: AbCd12345\n").deviceCode == "AbCd12345")
        // PTY reads can split after the fourth character of the second group.
        precondition(ProviderLoginParser.parse("Code: ABCD-EFGH").deviceCode == nil)
        precondition(ProviderLoginParser.parse("Code: ABCD-EFGH1\n").deviceCode == "ABCD-EFGH1")
    }
}
''',
                encoding="utf-8",
            )

            compiled = subprocess.run(
                ["swiftc", str(parser), str(harness), "-o", str(executable)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            completed = subprocess.run(
                [str(executable)], text=True, capture_output=True, check=False
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_device_login_watchdog_allows_the_bundled_connector_authorization_window(self) -> None:
        source = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        connector = (PROJECT_ROOT / "node_modules/openclaw/dist/extensions/openai/openai-chatgpt-device-code.js").read_text()
        monitor = source[source.index("private func monitorMerrickCodexLogin"):source.index("private func hasExistingOpenClawUserState")]

        # OpenClaw owns the 15-minute approval deadline. The GUI watchdog must
        # also allow startup and the final token exchange, not kill it at 3 min.
        self.assertIn("OPENAI_CODEX_DEVICE_CODE_TIMEOUT_MS = 15 * 6e4", connector)
        self.assertIn(".now() + 16 * 60", monitor)
        self.assertIn("provider.jarvis_oauth_timeout", monitor)

    def test_cancelled_device_login_cannot_publish_into_a_new_login(self) -> None:
        source = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        consume = source[source.index("private func consumeProviderLoginOutput"):source.index("private func startMerrickCodexDeviceConnection")]
        start = source[source.index("private func startMerrickCodexDeviceConnection"):source.index("private func cancelProviderConnection")]

        self.assertIn("from process: Process", consume)
        self.assertLess(consume.index("self.providerLoginProcess === process"), consume.index("self.providerLoginOutput ="))
        self.assertIn("consumeProviderLoginOutput(data, from: process)", start)
        # The read handler belongs to this pipe even after its login is cancelled.
        self.assertLess(start.index("output.fileHandleForReading.readabilityHandler = nil"), start.index("self.providerLoginProcess === process"))

    def test_provider_probe_parser_covers_every_supported_connection_route(self) -> None:
        parser = PROJECT_ROOT / "desktop" / "ProviderConnectionValidation.swift"
        generated_contract = PROJECT_ROOT / "desktop" / "RuntimeContract.generated.swift"
        with tempfile.TemporaryDirectory() as directory:
            harness = Path(directory) / "ProviderConnectionValidationHarness.swift"
            executable = Path(directory) / "provider-connection-validation-test"
            harness.write_text(
                r'''
import Foundation

@main
struct ProviderConnectionValidationHarness {
    static func main() {
        let routes: [String: String] = [
            "codex": "openai",
            "openai": "jarvis-openai-api",
            "claude-code": "claude-cli",
            "anthropic": "jarvis-anthropic-api",
            "gemini": "jarvis-google-api",
            "kimi": "jarvis-moonshot-api",
            "deepseek": "jarvis-compatible",
            "custom": "jarvis-compatible",
        ]
        for (provider, expected) in routes {
            precondition(ProviderProbeParser.probeProvider(for: provider) == expected)
        }

        let success = """
        warning: harmless prelude
        {
          "auth": {"probes": {"results": [
            {"provider":"openai","profileId":"openai:jarvis","status":"ok","latencyMs":321}
          ]}}
        }
        """
        let ready = ProviderProbeParser.parse(
            success,
            expectedProvider: "openai",
            expectedProfileID: "openai:jarvis"
        )
        precondition(ready.ready)
        precondition(ready.code == "READY")

        let wrongProfile = """
        {"auth":{"probes":{"results":[
          {"provider":"openai","profileId":"openai:default","status":"ok"}
        ]}}}
        """
        let rejectedShadow = ProviderProbeParser.parse(
            wrongProfile,
            expectedProvider: "openai",
            expectedProfileID: "openai:jarvis"
        )
        precondition(!rejectedShadow.ready)
        precondition(rejectedShadow.code == "PROFILE_NOT_PROBED")

        let unauthorized = """
        {"auth":{"probes":{"results":[
          {"provider":"anthropic","profileId":"anthropic:default","status":"error","error":"401 invalid authentication credentials"}
        ]}}}
        """
        let rejected = ProviderProbeParser.parse(
            unauthorized,
            expectedProvider: "anthropic"
        )
        precondition(!rejected.ready)
        precondition(rejected.code == "AUTH_REJECTED")

        let malformed = ProviderProbeParser.parse(
            "not json and not a probe",
            expectedProvider: "google"
        )
        precondition(!malformed.ready)
        precondition(malformed.code == "INVALID_PROBE_OUTPUT")
    }
}
''',
                encoding="utf-8",
            )

            compiled = subprocess.run(
                [
                    "swiftc",
                    str(generated_contract),
                    str(parser),
                    str(harness),
                    "-o",
                    str(executable),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            completed = subprocess.run(
                [str(executable)], text=True, capture_output=True, check=False
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_every_provider_connection_is_verified_before_it_is_committed(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        api = native[
            native.index("private func saveProviderAPIKey"):
            native.index("private func finishProviderOnboarding")
        ]
        oauth = native[
            native.index("private func completeMerrickCodexConnection"):
            native.index("private func monitorMerrickCodexLogin")
        ]
        cli = native[
            native.index("private func connectProviderCLI"):
            native.index("private func restartBackendForProviderChange")
        ]
        status = native[
            native.index("private func providerConnectionIsUsable"):
            native.index("private func completeMerrickCodexConnection")
        ]

        self.assertIn("validateCandidateProviderConnection", api)
        self.assertLess(
            api.index("validateCandidateProviderConnection"),
            api.index("commitValidatedProviderConnection"),
        )
        self.assertIn("validateCandidateProviderConnection", oauth)
        self.assertIn("validateClaudeCLIConnection", cli)
        self.assertIn("readProviderConnectionRecord", status)
        self.assertIn("providerLoginProcessGroup", native)
        self.assertIn("terminateProviderLoginProcessGroup", native)

    def test_oauth_probe_pauses_only_the_app_owned_gateway_and_restores_it_on_failure(self) -> None:
        native = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        validate = native[
            native.index("private func validateCandidateProviderConnection"):
            native.index("private func terminateProviderLoginProcessGroup")
        ]

        self.assertIn("pauseBackendForOAuthProbe", validate)
        self.assertLess(validate.index("pauseBackendForOAuthProbe"), validate.index("try process.run()"))
        self.assertIn("restoreBackendAfterOAuthProbe", validate)
        self.assertNotIn('process.arguments = [cli.entry.path, "gateway", "stop"]', validate)

        pause = native[
            native.index("private func pauseBackendForOAuthProbe"):
            native.index("private func validateCandidateProviderConnection")
        ]
        self.assertIn("terminateBackend", pause)
        self.assertIn("backendHealthTask?.cancel()", pause)
        self.assertIn("guard wasPaused, !outcome.ready", pause)
        self.assertIn('nativeTrace("provider.oauth_probe_gateway_paused")', pause)

    def test_intentional_backend_stop_cannot_trigger_crash_recovery(self) -> None:
        native = (PROJECT_ROOT / "desktop/MerrickApp.swift").read_text()
        terminate = native[
            native.index("private func terminateBackend(gracePeriod"):
            native.index("private func terminateBackendProcessGroup")
        ]

        self.assertLess(terminate.index("self.backend = nil"), terminate.index("backend.terminate()"))

    def test_runtime_provider_failure_invalidates_only_permanent_connections(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn('case "markProviderConnectionFailed"', native)
        self.assertIn("markProviderConnectionFailed(body)", native)
        self.assertIn('nativePost("markProviderConnectionFailed"', web)
        self.assertIn('"type": "provider_connection_issue"', backend)
        self.assertIn("failure.reconnect_required", backend)

    def test_native_app_exposes_a_real_quit_command(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("installApplicationMenu", native)
        self.assertIn('keyEquivalent: "q"', native)
        self.assertIn("#selector(NSApplication.terminate(_:))", native)

    def test_main_session_uses_direct_openclaw_execution_without_legacy_action_gate(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        config = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )

        self.assertIn("DIRECT_OPENCLAW_EXECUTION = True", backend)
        self.assertIn("not DIRECT_OPENCLAW_EXECUTION", backend)
        self.assertIn("DIRECT_OPENCLAW_EXECUTION_PROMPT", backend)
        self.assertIn('profile: "full"', config)
        self.assertIn('sandbox: "danger-full-access"', config)
        self.assertIn('approvalPolicy: "on-request"', config)
        self.assertIn('approvalsReviewer: "user"', config)
        self.assertNotIn('approvalsReviewer: "auto_review"', config)
        self.assertNotIn("codexDynamicToolsExclude", config)

    def test_local_desktop_requests_route_to_codex_computer_use_not_remote_nodes(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        local_prompt = backend[
            backend.index('LOCAL_COMPUTER_USE_EXECUTION_PROMPT = """'):
            backend.index('CONVERSATION_ONLY_PROMPT = """')
        ]
        prompt_selection = backend[
            backend.index("elif direct_openclaw_execution:"):
            backend.index("elif conversation_only:")
        ]

        self.assertIn("installed Codex-native Computer Use MCP directly", local_prompt)
        self.assertIn("native `tool_search`", local_prompt)
        self.assertIn("OpenClaw node-backed `computer`", local_prompt)
        self.assertIn("LOCAL_COMPUTER_USE_EXECUTION_PROMPT", prompt_selection)
        self.assertIn("if direct_desktop_candidate", prompt_selection)
        self.assertIn('self.openclaw_session_key = "jarvis-desktop-production-v17"', backend)

    def test_openclaw_capabilities_are_not_filtered_by_static_lists(self) -> None:
        config = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )

        # The sole allow entry is a transport exposure override for the bounded
        # persistent-session control plane; it does not filter the agent's
        # effective capability catalog.
        self.assertEqual(config.count('allow: ['), 1)
        self.assertIn('tools: { allow: ["sessions_spawn", "sessions_list", "sessions_history", "sessions"] }', config)
        self.assertIn('publicOrigin: "${JARVIS_OPENCLAW_PUBLIC_ORIGIN}"', config)
        self.assertNotIn('tools: { deny:', config)
        self.assertNotIn('deny: [', config)
        self.assertNotIn('alsoAllow:', config)
        self.assertIn('allow_all_plugins: true', config)
        self.assertIn('allow_destructive_actions: "ask"', config)

    def test_openclaw_action_approvals_are_visible_and_user_resolved(self) -> None:
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn('id="openclaw-approval"', html)
        self.assertIn('case "openclaw_approval_request"', web)
        self.assertIn('type: "openclaw_approval_response"', web)
        self.assertIn('mtype == "openclaw_approval_response"', backend)

    def test_direct_agent_bootstraps_an_app_owned_codex_computer_use_plugin(self) -> None:
        config = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )
        backend = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )
        bundle = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(
            encoding="utf-8"
        )
        common = (PROJECT_ROOT / "scripts" / "openclaw-common.sh").read_text(
            encoding="utf-8"
        )
        migration = (
            PROJECT_ROOT / "scripts" / "migrate-openclaw-codex-plugin.sh"
        ).read_text(encoding="utf-8")

        self.assertIn('computerUse: {', config)
        self.assertIn('autoInstall: true', config)
        self.assertIn('marketplacePath: "${JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH}"', config)
        self.assertIn('homeScope: "agent"', config)
        self.assertIn(
            'command: "${JARVIS_PROJECT_ROOT}/node_modules/.pnpm/node_modules/@openai/codex/bin/codex.js"',
            config,
        )
        self.assertNotIn(
            '"${JARVIS_PROJECT_ROOT}/node_modules/@openclaw/codex"',
            config,
        )
        self.assertIn('node_modules/openclaw/dist/extensions/codex', bundle)
        self.assertIn("_migrate_obsolete_codex_install_record", backend)
        self.assertIn("plugins uninstall codex --force --keep-files", migration)
        self.assertNotIn('"--disable",\n              "plugins"', config)
        self.assertIn("ensure_computer_use_runtime", backend)
        self.assertIn('"agents" / "main" / "agent" / "codex-home"', backend)
        self.assertIn('environment["OPENCLAW_CODEX_COMPUTER_USE"]', backend)
        self.assertIn("JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH", common)
        self.assertIn('codex-computer-use', bundle)
        self.assertTrue(
            (PROJECT_ROOT / "openclaw" / "codex-computer-use-marketplace" / ".agents" / "plugins" / "marketplace.json").is_file()
        )

    def test_computer_use_seed_uses_private_jarvis_state_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = (
                root
                / "codex-computer-use/client/Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
            )
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o700)
            manifest = root / "codex-computer-use/marketplace/.agents/plugins/marketplace.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name":"jarvis-bundled"}', encoding="utf-8")
            plugin_manifest = root / "codex-computer-use/marketplace/plugins/computer-use/.codex-plugin/plugin.json"
            plugin_manifest.parent.mkdir(parents=True)
            plugin_manifest.write_text('{"name":"computer-use"}', encoding="utf-8")

            gateway = OpenClawGateway()
            gateway.state_dir = root / "state"
            with mock.patch("openclaw_client.PROJECT_ROOT", root):
                first = gateway.ensure_computer_use_runtime()
                second = gateway.ensure_computer_use_runtime()

            expected = root / "state/agents/main/agent/codex-home/marketplaces/jarvis-bundled/.agents/plugins/marketplace.json"
            self.assertEqual(first, expected)
            self.assertEqual(second, expected)
            self.assertTrue(expected.is_file())
            self.assertTrue(
                (root / "state/agents/main/agent/codex-home/computer-use/Codex Computer Use.app").is_dir()
            )
            primary_executable = (
                root
                / "state/agents/main/agent/codex-home/computer-use/Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
            )
            for agent_id in ("conversation", "screen-reader", "action-planner", "researcher"):
                private_runtime = root / f"state/agents/{agent_id}/agent/codex-home/computer-use"
                self.assertTrue(private_runtime.is_dir(), private_runtime)
                self.assertFalse(private_runtime.is_symlink(), private_runtime)
                private_executable = (
                    private_runtime
                    / "Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
                )
                self.assertEqual(primary_executable.stat().st_ino, private_executable.stat().st_ino)

    def test_distribution_packaging_validates_the_user_launchable_bundle(self) -> None:
        source = (PROJECT_ROOT / "scripts" / "package-macos-app.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('codesign --verify --deep --strict --verbose=2 "$APP"', source)
        self.assertIn('plutil -lint "$APP/Contents/Info.plist"', source)
        self.assertIn('test -x "$APP/Contents/MacOS/Merrick"', source)
        self.assertIn('test -d "$APP/Contents/Resources/runtime"', source)

    def test_distribution_runs_the_embedded_runtime_preflight_before_dmg_creation(self) -> None:
        package = (PROJECT_ROOT / "scripts" / "package-macos-app.sh").read_text(
            encoding="utf-8"
        )
        verifier_path = PROJECT_ROOT / "scripts" / "verify-macos-release.sh"

        self.assertTrue(verifier_path.is_file())
        verifier = verifier_path.read_text(encoding="utf-8")
        self.assertIn('verify-macos-release.sh" "$APP"', package)
        self.assertIn("codesign --verify --deep --strict", verifier)
        self.assertIn(".venv/bin/python", verifier)
        self.assertIn("node/bin/node", verifier)
        self.assertIn("@openai/codex/bin/codex.js", verifier)
        self.assertIn("scripts/uninstall-merrick.sh", verifier)
        self.assertIn("scripts/setup-openclaw.sh", verifier)
        self.assertIn("OPENCLAW_STATE_DIR", verifier)
        self.assertIn("ERR_PNPM_NO_PKG_MANIFEST", verifier)
        self.assertIn("plugin not installed: codex", verifier)
        self.assertIn("openKeyedStore is only available for trusted plugins", verifier)
        self.assertIn('plugin["origin"] == "bundled"', verifier)
        self.assertIn('plugin["status"] == "loaded"', verifier)

    def test_release_copies_openclaw_manifests_and_never_installs_packages_at_runtime(self) -> None:
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(
            encoding="utf-8"
        )
        setup = (PROJECT_ROOT / "scripts" / "setup-openclaw.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('for runtimeFile in package.json pnpm-lock.yaml pnpm-workspace.yaml', build)
        self.assertIn('node_modules/openclaw/dist/extensions/codex', build)
        self.assertIn('JARVIS_BUNDLED_RUNTIME', setup)
        self.assertIn('"$NODE_BIN" "$OPENCLAW_CLI" config validate', setup)
        bundled_start = setup.index('if [ "$JARVIS_BUNDLED_RUNTIME" = "1" ]')
        bundled_branch = setup[bundled_start:setup.index("\nelse\n", bundled_start)]
        self.assertNotIn('"$PNPM_BIN" install', bundled_branch)

    def test_public_distribution_requires_developer_id_and_notarization(self) -> None:
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(
            encoding="utf-8"
        )
        package = (PROJECT_ROOT / "scripts" / "package-macos-app.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("JARVIS_CODESIGN_IDENTITY", build)
        self.assertIn("--options runtime", build)
        self.assertIn("JARVIS_PUBLIC_RELEASE", package)
        self.assertIn("JARVIS_NOTARY_PROFILE", package)
        self.assertIn("security find-identity", package)
        self.assertIn("notarytool submit", package)
        self.assertIn("stapler staple", package)
        self.assertIn("spctl --assess", package)

    def test_release_build_removes_workspace_only_dangling_symlinks(self) -> None:
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn('find "$RUNTIME/node_modules" -type l', build)
        self.assertIn("-delete", build)

    def test_distribution_packaging_removes_the_temporary_duplicate_after_the_dmg_exists(self) -> None:
        source = (PROJECT_ROOT / "scripts" / "package-macos-app.sh").read_text(
            encoding="utf-8"
        )

        self.assertGreater(
            source.rfind('rm -rf "$STAGE"'),
            source.index('hdiutil create -volname "MERRICK"'),
        )

    def test_interface_startup_has_a_bounded_bridge_readiness_watchdog(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("webReadyTimeoutWorkItem", source)
        self.assertIn("scheduleWebReadyTimeout", source)
        self.assertIn("interface.bridge_timeout", source)
        self.assertIn("The MERRICK interface did not finish loading", source)

    def test_interface_bridge_timeout_reloads_once_before_showing_failure(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        watchdog = source[
            source.index("private func scheduleWebReadyTimeout"):
            source.index("private var expectedBridgeProof")
        ]

        self.assertIn("maximumWebLoadAttempts", source)
        self.assertIn("webView.stopLoading()", watchdog)
        self.assertIn("loadHUDOnce()", watchdog)
        self.assertIn("interface.bridge_reload", watchdog)

    def test_backend_startup_failure_cleans_owned_runtime_and_retries_once(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("private let maximumBackendStartupAttempts = 2", source)
        self.assertIn("private func recoverBackendStartup", source)
        recovery = source[
            source.index("private func recoverBackendStartup"):
            source.index("private func pollBackendHealth")
        ]
        self.assertIn("terminateBackend(gracePeriod: 2.0)", recovery)
        self.assertIn("reclaimOrphanedRuntimeProcesses()", recovery)
        self.assertIn("startBackend()", recovery)

    def test_backend_crash_after_launch_uses_the_same_bounded_recovery(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        start = source.index("private func startBackend")
        handler_start = source.index("process.terminationHandler =", start)
        handler = source[handler_start:source.index("do {", handler_start)]
        health = source[
            source.index("private func pollBackendHealth"):
            source.index("private func loadHUDOnce")
        ]

        self.assertIn("recoverBackendStartup", handler)
        self.assertNotIn("if !self.hudLoadStarted", handler)
        self.assertIn("backendStartupAttempts = 0", health)

    def test_backend_recovery_has_a_restart_storm_circuit_breaker(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        recovery = source[
            source.index("private func recoverBackendStartup"):
            source.index("private func pollBackendHealth")
        ]

        self.assertIn("backendRecoveryHistory", source)
        self.assertIn("maximumBackendRecoveriesPerWindow", source)
        self.assertIn("backend.recovery_circuit_open", recovery)

    def test_launch_reclaims_orphans_from_an_older_installed_bundle_path(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        reclaim = source[
            source.index("private func reclaimOrphanedRuntimeProcesses"):
            source.index("private func buildWindow")
        ]

        self.assertIn('"/Contents/Resources/runtime/"', reclaim)
        self.assertIn("steadfast_tts_worker.py", reclaim)
        self.assertIn("audio_isolation_worker.py", reclaim)

    def test_orphan_cleanup_checks_kernel_executable_and_bundle_identity(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text()
        reclaim = source[
            source.index("private func reclaimOrphanedRuntimeProcesses"):
            source.index("private func buildWindow")
        ]

        self.assertIn("merrickRuntimeExecutablePath", reclaim)
        self.assertIn("merrickOwnsRuntimeExecutable", reclaim)
        self.assertNotIn("command.contains(bundledRuntimeMarker)", reclaim)

    def test_build_requires_runtime_isolation_regressions_to_pass(self) -> None:
        build = (PROJECT_ROOT / "scripts/build-macos-app.sh").read_text()
        self.assertTrue('tests/test_uninstall_process_ownership.py' in build)
        self.assertTrue('tests/test_native_runtime_ownership.py' in build)
        self.assertTrue('tests/test_gateway_identity.py' in build)

    def test_launch_from_installer_volume_redirects_to_the_installed_copy(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        launch = source[
            source.index("func applicationDidFinishLaunching"):
            source.index("private func rememberFrontmostApplication")
        ]

        self.assertIn("redirectInstallerVolumeLaunchIfNeeded", launch)
        self.assertIn('hasPrefix("/Volumes/")', launch)
        self.assertIn('"/Applications/MERRICK.app"', launch)
        self.assertIn("installedBundle.bundleIdentifier == Bundle.main.bundleIdentifier", launch)
        self.assertIn("installer_launch_redirected", launch)
        self.assertLess(
            launch.index("redirectInstallerVolumeLaunchIfNeeded"),
            launch.index("redirectToExistingInstanceIfNeeded"),
        )

    def test_confirmed_uninstall_removes_owned_processes_credentials_data_and_app(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        uninstaller_path = PROJECT_ROOT / "scripts" / "uninstall-merrick.sh"

        self.assertTrue(uninstaller_path.is_file())
        uninstaller = uninstaller_path.read_text(encoding="utf-8")
        self.assertIn('EXPECTED_BUNDLE_ID="ai.jarvis.desktop"', uninstaller)
        self.assertIn('Library/Application Support/JarvisStark', uninstaller)
        self.assertIn('Library/Caches/JarvisStark', uninstaller)
        self.assertIn('Library/Application Support/CrashReporter', uninstaller)
        self.assertIn("-name 'Jarvis_*.plist'", uninstaller)
        self.assertIn('ai.jarvis.desktop.provider-credentials', uninstaller)
        self.assertIn("tccutil reset", uninstaller)
        self.assertIn("SIGKILL", uninstaller)
        self.assertIn('case "uninstall":', native)
        self.assertIn("confirmAndUninstall", native)
        self.assertIn('id="uninstall-btn"', markup)
        self.assertIn('nativePost("uninstall")', web)

    def test_renderer_distinguishes_model_connection_from_generic_booting(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('connecting: "state_connecting"', source)
        self.assertIn('state_connecting: "CONNECTING MODEL"', source)
        self.assertIn('serverState = "connecting"', source)

    def test_hud_close_requests_a_complete_quit(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('nativePost("quit")', source)
        self.assertNotIn('nativePost("hide")', source)

    def test_native_quit_terminates_and_cleans_up_owned_processes(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn('case "quit":', source)
        self.assertIn("NSApp.terminate(nil)", source)
        self.assertNotIn("window.orderOut(nil)", source)
        self.assertIn("stopListening(final: false)", source)
        self.assertIn("terminateBackend()", source)

    def test_backend_and_openclaw_share_one_native_owned_process_group(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        gateway = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("private var backendProcessGroup: pid_t?", native)
        self.assertIn("Darwin.getpgid(process.processIdentifier)", native)
        self.assertIn("terminateBackendProcessGroup()", native)
        self.assertNotIn("start_new_session=True", gateway)

    def test_audio_isolation_worker_shutdown_is_synchronous_and_bounded(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        worker = native[
            native.index("private final class AudioIsolationWorker"):
            native.index("private struct ProviderProfile")
        ]

        self.assertIn("queue.sync", worker)
        self.assertIn("audio_worker_force_kill", worker)
        self.assertIn("Date().addingTimeInterval", worker)

    def test_websocket_and_runtime_shutdown_each_use_one_total_budget(self) -> None:
        backend = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        session_shutdown = backend[
            backend.index("    async def run(self, *, subprotocol: str | None = None):"):
            backend.index("\n\n@asynccontextmanager", backend.index("    async def run(self, *, subprotocol: str | None = None):"))
        ]
        lifespan = backend[
            backend.index("async def app_lifespan"):
            backend.index("\n\napp = FastAPI", backend.index("async def app_lifespan"))
        ]

        self.assertIn("run_bounded_shutdown_steps", session_shutdown)
        self.assertIn("SESSION_SHUTDOWN_BUDGET_SECONDS", session_shutdown)
        self.assertIn("run_bounded_shutdown_steps", lifespan)
        self.assertIn("RUNTIME_SHUTDOWN_BUDGET_SECONDS", lifespan)

    def test_native_backend_uses_the_project_venv_without_a_uv_wrapper(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn('appendingPathComponent(".venv/bin/python")', source)
        self.assertIn('process.executableURL = venvPython', source)
        self.assertIn('process.arguments = uvicornArguments', source)

    def test_window_close_semantics_are_quit_not_hide(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn("NSWindowDelegate", source)
        self.assertIn("func windowShouldClose", source)
        self.assertIn("func applicationShouldTerminateAfterLastWindowClosed", source)

    def test_native_background_drag_does_not_steal_clicks_from_web_form_controls(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("window.isMovableByWindowBackground = false", native)
        self.assertNotIn("window.isMovableByWindowBackground = true", native)
        self.assertIn(
            'target.closest("button, input, textarea, select, a, label, .panel, .hud-footer")',
            frontend,
        )
        self.assertIn('nativePost("moveWindow", { dx, dy })', frontend)

    def test_borderless_hud_can_become_key_so_web_text_fields_accept_mouse_focus(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("private final class MerrickHUDWindow: NSWindow", native)
        self.assertIn("override var canBecomeKey: Bool { true }", native)
        self.assertIn("override var canBecomeMain: Bool { true }", native)
        self.assertIn("window = MerrickHUDWindow(contentRect:", native)

    def test_expanding_the_hud_keeps_the_entire_form_on_screen(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("private func fullyVisibleOrigin(", native)
        resize = native[native.index("private func resize(expanded:"):]
        resize = resize[:resize.index("/// A persisted HUD position")]
        self.assertIn("fullyVisibleOrigin(frame.origin, size: size, on: targetScreen)", resize)
        self.assertLess(
            resize.index("fullyVisibleOrigin(frame.origin, size: size, on: targetScreen)"),
            resize.index("window.setFrame(frame, display: true, animate: true)"),
        )

    def test_native_application_aliases_include_singular_map(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn('"map": "maps"', source)
        self.assertIn("knownApplicationBundleIDs[targetName]", source)

    def test_app_focus_is_verified_before_reporting_success(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn("confirmApplicationFocus", source)
        self.assertIn("frontmostApplication?.processIdentifier", source)
        self.assertIn("did not come to the front", source)

    def test_barge_in_accepts_stop_or_two_stable_non_echo_words(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const confirmedStop = stopCommand && recentAcousticEvidence", source)
        self.assertIn("const chineseStopCommand", source)
        self.assertIn("[\\u3400-\\u9fff]", source)
        self.assertIn("novelWords.length >= 2", source)
        self.assertIn("const echoDensity = matchedWordCount", source)
        self.assertIn("const echoDominated = echoDensity >= 0.62", source)
        self.assertIn("const unsafeMixedEcho = !bargeEchoCancellationActive", source)
        self.assertIn("!unsafeMixedEcho && acousticEvidence", source)
        self.assertIn("const fastIndependentPhrase = novelWords.length >= 2", source)
        self.assertIn('sendJson({ type: "interrupt" })', source)

    def test_clean_barge_recovers_new_words_instead_of_holding_input_indefinitely(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function novelTranscriptWordsAfterBaseline", source)
        self.assertIn("const recovered = novelTranscriptWordsAfterBaseline", source)
        self.assertIn("text = recovered", source)
        self.assertIn("cleanBargeTranscriptBaseline = \"\"", source)

    def test_latency_changes_start_tool_free_voice_preflight_without_generic_ack(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn("DRAFT_PREFLIGHT_SECONDS = 0.40", source)
        self.assertIn("DRAFT_COMMIT_SECONDS = 1.05", source)
        self.assertIn("VOICE_DRAFT_PREFLIGHT_MIN_CHARS = 44", source)
        self.assertIn("latency.gateway_preflight_ready", source)
        self.assertIn("latency.model_draft_preflight_started", source)
        self.assertIn("is_voice_draft_preflight_candidate", source)
        self.assertIn('"voice_preflight": True', source)
        self.assertIn('await self.send({"type": "status", "state": "thinking"})', source)
        self.assertNotIn("await self.send_fast_acknowledgement(fast_ack_kind)", source)
        self.assertIn("self.start_turn_understanding(", source)
        self.assertIn("await wait_for_draft_commit()", source)
        self.assertIn(
            "output_started = not action_protocol_enabled and not is_draft", source
        )
        self.assertIn("if action_protocol_enabled or is_draft:", source)
        self.assertIn("await openclaw_gateway.prewarm()", source)

    def test_incremental_tts_has_capability_negotiation_and_complete_audio_fallback(self) -> None:
        server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        tts = (PROJECT_ROOT / "server" / "tts.py").read_text(encoding="utf-8")
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('mtype == "set_tts_streaming"', server)
        self.assertIn("send_streaming_tts_audio", server)
        self.assertIn('"type": "audio_stream_chunk"', server)
        self.assertIn('type: "set_tts_streaming"', web)
        self.assertIn("supportsIncrementalTtsAudio", web)
        self.assertIn("promoteStreamFallback", web)
        self.assertIn('audio/pcm;format=s16le', tts)
        self.assertIn("enqueuePcmAudioStreamChunk", web)
        self.assertIn("schedulePcmAudioChunks", web)
        self.assertIn("createBuffer", web)

    def test_pcm_stream_buffers_before_playback_and_softens_only_real_underruns(self) -> None:
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("PCM_INITIAL_BUFFER_SECONDS", web)
        self.assertIn("pendingPcmDurationSeconds", web)
        self.assertIn("pendingDuration < PCM_INITIAL_BUFFER_SECONDS", web)
        self.assertIn("const underrun = item.playbackSignalled", web)
        self.assertIn("context.createGain()", web)
        self.assertIn("linearRampToValueAtTime", web)

    def test_plain_conversation_uses_the_persistent_gateway_lane(self) -> None:
        server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        client = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("stream_conversation_response", server)
        self.assertIn('"chat.send"', client)
        self.assertIn("event_subscription", client)

    def test_first_tts_segment_warms_audio_output_before_playback(self) -> None:
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("async function warmAudioOutput", web)
        self.assertIn("await warmAudioOutput()", web)
        self.assertIn("firstSegmentAfterIdle", web)
        self.assertIn("audio_output_warmed", web)

    def test_microphone_button_can_override_automatic_listening(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("let listeningManuallyMuted = false", source)
        self.assertIn("if (listeningManuallyMuted || !autoToggle.checked", source)
        self.assertIn("listeningManuallyMuted = true", source)

    def test_processing_state_wins_while_native_recognizer_is_stopping(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index("function refreshUiState()")
        end = source.index("\n}\n", start)
        refresh = source[start:end]
        working = 'if (serverState === "thinking" || serverState === "acting")'
        listening = 'if (recognizing) return setUiState("listening")'
        self.assertIn(working, refresh)
        self.assertLess(refresh.index(working), refresh.index(listening))

    def test_new_conversation_turn_clears_the_previous_research_display_title(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index('case "turn":')
        end = source.index('case "assistant_delta":', start)
        turn_handler = source[start:end]

        self.assertIn('researchQuery.textContent = t("live_answer")', turn_handler)
        self.assertIn('delete researchQuery.dataset.i18nDynamic', turn_handler)

    def test_openclaw_config_uses_secret_refs_for_gateway_and_compatible_api_keys(self) -> None:
        config = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'token: { source: "env", provider: "default", id: "OPENCLAW_GATEWAY_TOKEN" }',
            config,
        )
        self.assertIn(
            'apiKey: { source: "env", provider: "default", id: "JARVIS_MODEL_API_KEY" }',
            config,
        )

    def test_language_switch_relocalizes_dynamic_settings_statuses(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index("function applyInterfaceLanguage(language)")
        end = source.index("\n}\n", start)
        language_handler = source[start:end]

        self.assertIn("renderAutomationAccessState(automationAccessState)", language_handler)
        self.assertIn('addressStatus?.dataset.state === "ready"', language_handler)

    def test_native_notification_denial_uses_the_current_interface_language(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index("window.merrickNativeNotificationStatus = function")
        end = source.index("window.merrickNativeScreenCaptureResult", start)
        handler = source[start:end]

        self.assertIn('message === "Enable notifications for MERRICK in System Settings."', handler)
        self.assertIn('oc("notificationDenied")', handler)

    def test_voice_opened_dashboard_expands_the_desktop_hud(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        start = source.index("function setOrganizerVisible(")
        end = source.index("\n}\n", start)
        organizer = source[start:end]
        self.assertIn('document.body.classList.add("expanded")', organizer)
        self.assertIn('nativePost("resize", { expanded: true })', organizer)

    def test_newspaper_reader_has_focus_mode_and_native_fullscreen_controls(self) -> None:
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")

        self.assertIn('id="organizer-fullscreen-btn"', markup)
        self.assertIn("function enterNewspaperFocus", web)
        self.assertIn("function exitNewspaperFocus", web)
        self.assertIn('nativePost("setWindowFullscreen", { mode, requestId })', web)
        self.assertIn('event.key === "Escape" && newspaperFocusActive', web)
        self.assertIn('event.code === "KeyF" && event.ctrlKey && event.metaKey', web)
        self.assertIn("window.merrickNativeFullscreenState", web)
        self.assertIn(".organizer-panel.newspaper-focus", style)
        self.assertIn(".intelligence-reader-toolbar", style)
        self.assertIn("width: min(1500px", style)

    def test_native_fullscreen_bridge_is_bounded_and_restores_hud_behavior(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn('case "setWindowFullscreen":', source)
        self.assertIn('["enter", "exit", "toggle"].contains(requestedMode)', source)
        self.assertIn("UUID(uuidString: requestID) != nil", source)
        self.assertIn("window.toggleFullScreen(nil)", source)
        self.assertIn("fullscreenBehavior.insert(.fullScreenPrimary)", source)
        self.assertIn("func windowDidEnterFullScreen", source)
        self.assertIn("func windowDidExitFullScreen", source)
        self.assertIn("restoreHUDWindowBehavior()", source)
        self.assertIn("window.merrickNativeFullscreenState", source)

    def test_project_cards_offer_bounded_edit_and_confirmed_archive_controls(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn('type: "organizer_rename_project"', source)
        self.assertIn('type: "organizer_archive_project"', source)
        self.assertIn('confirmed: true', source)
        self.assertIn("organizer-project-delete-confirm", source)
        self.assertIn('card.scrollIntoView({ block: "nearest" })', source)
        self.assertIn(".organizer-project-actions[hidden]", style)
        self.assertIn("white-space: normal", style)
        self.assertIn("overflow-wrap: anywhere", style)

    def test_organizer_lists_are_viewport_bounded_scrollable_and_proportional(self) -> None:
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn('data-organizer-page="overview" tabindex="0"', markup)
        self.assertIn(".organizer-view {", style)
        self.assertIn("overflow-x: hidden; overflow-y: auto", style)
        self.assertIn("overscroll-behavior: contain", style)
        self.assertIn("scrollbar-gutter: stable", style)
        self.assertIn("#organizer-task-list { max-height: clamp", style)
        self.assertIn("#organizer-reminder-list { max-height: clamp", style)
        self.assertIn("#organizer-project-list { max-height: clamp", style)
        self.assertIn("--organizer-body-size: clamp", style)
        self.assertIn("@media (max-height: 720px)", style)

    def test_organizer_project_actions_remain_visually_secondary_and_compact(self) -> None:
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn("--organizer-action-size: .8rem", style)
        self.assertIn("--organizer-inline-action-size: .8rem", style)
        self.assertIn("min-height: 30px; padding: 5px 9px", style)
        self.assertIn("flex-wrap: wrap", style)
        self.assertIn("background: transparent", style)
        self.assertIn("background: rgba(91,25,35,.16)", style)
        self.assertIn(":where(button, input, select):focus-visible", style)
        self.assertIn("white-space: normal; overflow-wrap: anywhere", style)
        self.assertIn(".clock { display: none; }", style)
        self.assertIn(".header-right { min-width: 0", style)

    def test_hologram_palette_is_not_bound_to_system_appearance(self) -> None:
        source = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertNotIn("@media (prefers-color-scheme", source)
        self.assertIn("filter: brightness(.47) contrast(1.48) saturate(1.62)", source)

    def test_connection_retries_do_not_dim_the_hologram(self) -> None:
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('let serverState = "booting"', source)
        self.assertIn('setUiState("booting")', source)
        self.assertIn("const dim = 1;", source)
        self.assertNotIn('uiState === "offline" ? 0.35 : 1', source)

    def test_hud_controls_wrap_without_button_or_translation_clipping(self) -> None:
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('class="command-compose"', markup)
        self.assertIn('class="footer-actions"', markup)
        self.assertIn(".footer-actions {", style)
        self.assertIn("flex-wrap: wrap", style)
        self.assertIn("grid-template-columns: 46px minmax(0, 1fr) max-content", style)
        self.assertIn("overflow-wrap: anywhere", style)
        self.assertNotIn("text-overflow: ellipsis", style)
        self.assertIn('command_placeholder: "Instruction… (Enter to send)"', source)

    def test_watch_mode_has_an_expanded_owner_only_control(self) -> None:
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        style = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")
        self.assertIn('id="watch-mode-btn"', markup)
        self.assertIn("set_owner_only_mode", source)
        self.assertIn("watch_owner", source)
        self.assertIn("msg.watch_owner === true", source)
        self.assertIn("full_retry", source)
        self.assertIn("furthest complete phrase", source)
        self.assertIn("looksLikeAssistantEchoText", source)
        self.assertIn("restartListening", source)
        self.assertIn("body.desktop.expanded .watch-mode-btn", style)

    def test_native_watch_mode_can_restart_a_clean_recognition_turn(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('case "restartListening":', source)
        self.assertIn('case "beginWatchVoiceVerification":', source)
        self.assertIn("watch.voice_sample_gate_released", source)
        self.assertIn('case "setWatchAudioMode":', source)
        self.assertIn("stopListening(final: false)", source)
        self.assertIn("configureInputVoiceProcessing", source)
        self.assertIn("watch.audio_isolation requested", source)
        self.assertIn("startPlaybackIsolationIfPossible", source)
        self.assertIn("audio_isolation_worker.py", source)
        self.assertIn("let wantsVoiceProcessing = requestedVoiceProcessing", source)
        self.assertIn('nativePost("setWatchAudioMode"', web)

    def test_system_playback_filter_stays_active_for_normal_conversation(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )

        self.assertIn("private var systemAudioFilterActivated = false", source)
        self.assertIn("private func activateSystemAudioFilterIfNeeded()", source)
        self.assertIn("activateSystemAudioFilterIfNeeded()", source)
        isolation = source[source.index("private func updatePlaybackIsolation()") :]
        isolation = isolation[: isolation.index("private func startPlaybackIsolationIfPossible()")]
        self.assertIn("systemAudioFilterActivated", isolation)
        self.assertIn("assistantAudioPlaying", isolation)
        self.assertIn("playbackReferenceRequested", isolation)
        self.assertIn("config.excludesCurrentProcessAudio = false", source)
        self.assertIn('object["playback_suppressed"] as? Bool ?? false', source)
        info = (PROJECT_ROOT / "desktop" / "Info.plist").read_text(encoding="utf-8")
        self.assertIn("NSAudioCaptureUsageDescription", info)
        self.assertIn("NSScreenCaptureUsageDescription", info)

    def test_external_system_audio_requires_an_explicit_jarvis_wake_word(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("updateSystemPlaybackActivity", native)
        self.assertIn("window.merrickNativeSystemAudioActivity", native)
        self.assertIn("function externalPlaybackCommandFromTranscript", web)
        self.assertIn("let externalPlaybackCommandActive = false", web)
        transcript_handler = web[web.index("window.merrickNativeTranscript = function") :]
        transcript_handler = transcript_handler[: transcript_handler.index("window.merrickNativeVoiceActivity")]
        self.assertIn("externalPlaybackGateForTurn && !audioPlaying", transcript_handler)
        self.assertIn(
            "externalPlaybackGateForTurn = systemPlaybackActive && !audioPlaying",
            web,
        )
        self.assertIn("external_playback_transcript_blocked", transcript_handler)
        self.assertIn("externalPlaybackCommandFromTranscript", transcript_handler)

    def test_external_playback_gate_releases_only_new_speech_after_media_stops(self) -> None:
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("let externalPlaybackTranscriptBaseline = \"\"", web)
        self.assertIn("function recoverTranscriptAfterPlaybackStops", web)
        transcript_handler = web[web.index("window.merrickNativeTranscript = function") :]
        transcript_handler = transcript_handler[
            : transcript_handler.index("window.merrickNativeVoiceActivity")
        ]
        self.assertIn("recoverTranscriptAfterPlaybackStops", transcript_handler)
        self.assertIn("external_playback_gate_recovered", transcript_handler)
        self.assertIn('type: "runtime_stall"', transcript_handler)
        self.assertIn('subsystem: "voice_pipeline"', transcript_handler)
        self.assertIn('code: "external_playback_gate_stalled"', transcript_handler)

    def test_native_clean_voice_edge_waits_for_transcript_novelty(self) -> None:
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("let pendingNativeCleanVoiceActivity = false", web)
        handler = web[web.index("window.merrickNativeVoiceActivity = function") :]
        handler = handler[: handler.index("window.merrickNativeCleanBargeIn")]
        self.assertIn("pendingNativeCleanVoiceActivity = true", handler)
        self.assertNotIn(
            'sendJson({ type: "voice_activity", active: Boolean(active)',
            handler,
        )
        transcript_handler = web[web.index("window.merrickNativeTranscript = function") :]
        transcript_handler = transcript_handler[
            : transcript_handler.index("window.merrickNativeVoiceActivity")
        ]
        self.assertIn("confirmPendingNativeCleanVoice", transcript_handler)

    def test_mode_specific_barge_in_keeps_watch_owner_only_and_meeting_wake_only(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn("beginWatchVoiceVerification", native)
        self.assertIn("watch.voice_verification_started", native)
        self.assertIn("meetingCleanVoiceActive", web)
        self.assertIn('type: "meeting_command_interrupt"', web)
        self.assertIn('mtype == "meeting_command_interrupt"', server)
        self.assertIn("source=\"meeting_wake\"", server)

    def test_meeting_mode_records_without_answering_until_jarvis_is_addressed(self) -> None:
        markup = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        source = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn('id="meeting-mode-btn"', markup)
        self.assertIn('type: "meeting_transcript"', source)
        self.assertIn("meetingCommandFromTranscript", source)
        self.assertIn("meeting_wake_detected", source)
        self.assertIn("recent_wake_word", source)
        self.assertIn("queueMeetingTranscript", source)
        self.assertIn("flushMeetingTranscript", source)
        self.assertIn("meetingPendingTranscript", source)
        self.assertIn("MEETING_MERRICK_ADDRESS_RE", server)
        self.assertIn("jarviz", server)
        self.assertIn("recent_meeting_context", server)

    def test_visible_search_uses_the_same_provider_as_followup_results(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn('URLComponents(string: "https://www.google.com/search")', source)
        self.assertNotIn('URLComponents(string: "https://duckduckgo.com/")', source)

    def test_host_selected_public_result_can_open_in_the_requested_browser(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(
            encoding="utf-8"
        )
        self.assertIn('case "browser_open_url"', source)
        self.assertIn("isValidPublicWebURL", source)
        self.assertIn("case .browserOpenURL", source)

    def test_gateway_leaves_codex_workspace_write_sandbox_available(self) -> None:
        source = (PROJECT_ROOT / "scripts" / "run-openclaw-gateway.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('Codex app-server enforces workspace-write itself', source)
        self.assertNotIn('exec /usr/bin/sandbox-exec', source)
        self.assertIn('OPENCLAW_SUPERVISOR_MODE="external"', source)
        self.assertIn('OPENCLAW_NO_RESPAWN="1"', source)

    def test_workspace_requests_bypass_desktop_action_protocol(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn("WORKSPACE_CONTROL_PROMPT", source)
        self.assertIn(
            "not DIRECT_OPENCLAW_EXECUTION\n            and openclaw_action_candidate",
            source,
        )
        self.assertIn("Codex native workspace tools", source)

    def test_workspace_intent_requires_a_workspace_or_document_work_request(self) -> None:
        self.assertTrue(workspace_control_intent("Create a note in the Merrick workspace."))
        self.assertTrue(workspace_control_intent("Please update the project draft."))
        self.assertTrue(workspace_control_intent("Write a summary of the paper."))
        self.assertFalse(
            workspace_control_intent(
                "Write an original report in this reply. Do not save or create a file."
            )
        )
        self.assertTrue(workspace_control_intent("Read a file in the Merrick workspace."))
        self.assertFalse(workspace_control_intent("Read the file."))
        self.assertFalse(workspace_control_intent("List my files."))
        self.assertFalse(workspace_control_intent("What is the weather today?"))

    def test_main_agent_exposes_full_openclaw_capabilities_under_desktop_authorization(self) -> None:
        source = (PROJECT_ROOT / "openclaw" / "openclaw.template.json5").read_text(
            encoding="utf-8"
        )
        global_tools = source[
            source.index("\n  tools: {", source.index("\n  memory: {")):
            source.index("\n  transcripts:")
        ]
        self.assertIn('profile: "full"', source)
        self.assertNotIn("alsoAllow:", global_tools)
        self.assertIn('fs: { workspaceOnly: false }', source)
        self.assertIn('exec: { mode: "full" }', source)
        self.assertIn('elevated: { enabled: true }', source)
        self.assertIn('codeMode: { enabled: true }', source)
        self.assertIn("browser: {", source)
        self.assertIn("computerUse: {", source)

    def test_voice_workspace_is_isolated_from_operational_files(self) -> None:
        source = (PROJECT_ROOT / "scripts" / "openclaw-common.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('JarvisStark/Workspace/Documents', source)

    def test_desktop_setup_uses_native_workspace_and_authenticated_voiceprint_capture(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("import LocalAuthentication", source)
        self.assertIn(".deviceOwnerAuthentication", source)
        self.assertIn('case "openWorkspace"', source)
        self.assertIn('case "captureVoiceprintSample"', source)
        self.assertIn("YOUR DOCUMENTS", frontend)
        self.assertIn("OPENCLAW CAPABILITIES", frontend)
        self.assertIn('id="capabilities-open-btn"', frontend)

    def test_openclaw_control_ui_handoff_stays_native_and_targets_owned_gateway(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        script = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="open-openclaw-dashboard-btn"', frontend)
        self.assertIn('nativePost("openOpenClawDashboard")', script)
        self.assertIn('case "openOpenClawDashboard"', native)
        self.assertIn('environment["OPENCLAW_GATEWAY_URL"]', native)
        self.assertIn('environment["OPENCLAW_GATEWAY_PORT"]', native)
        self.assertIn('environment["OPENCLAW_GATEWAY_TOKEN"] = gatewayToken', native)
        self.assertIn('.appendingPathComponent("OpenClaw/.gateway-token")', native)
        self.assertIn('["dashboard", "--json", "--no-open"]', native)
        self.assertIn('ownerPort == dashboardPort', native)
        self.assertIn('host == "127.0.0.1" || host == "localhost"', native)
        self.assertIn('sessionURL.path.hasPrefix("/chat/")', native)
        self.assertIn('destination.path = route.path', native)
        self.assertIn('NSWorkspace.shared.open(destinationURL)', native)
        self.assertIn('openAuthenticatedOpenClawControl(route: sessionURL', native)
        self.assertNotIn('jsString(browserURL.absoluteString)', native)
        self.assertNotIn('jsString(gatewayToken)', native)
        self.assertIn('id="capability-review"', frontend)
        self.assertIn('type: "capability_review_request"', script)
        self.assertIn('type: "capability_review_apply"', script)
        self.assertNotIn('type: "capability_toggle"', script)

    def test_codex_connection_stays_inside_jarvis_instead_of_opening_terminal(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("startMerrickCodexDeviceConnection", source)
        self.assertIn("process.standardOutput = output", source)
        self.assertIn("process.standardError = output", source)
        self.assertIn("merrickNativeProviderSetupProgress", source)
        self.assertNotIn("NSWorkspace.shared.open(loginScript)", source)
        self.assertIn("deviceCode", frontend)
        self.assertIn("verificationURL", frontend)

    def test_direct_automation_uses_a_user_chosen_root_and_local_audit(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn('case "chooseAutomationAccessRoot"', native)
        self.assertIn('case "saveAutomationAccessPolicy"', native)
        self.assertIn("automationAccessProfile", native)
        self.assertIn("JARVIS_WORKSPACE_DIR", native)
        self.assertIn('id="automation-access-root"', frontend)
        self.assertIn('id="automation-access-enable"', frontend)
        self.assertIn("WorkspaceMutationAudit", server)

    def test_desktop_supports_bounded_accessibility_gui_interactions(self) -> None:
        source = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("AXIsProcessTrustedWithOptions", source)
        self.assertIn("case .guiInteraction", source)
        self.assertIn('case "gui_interaction"', frontend)

    def test_plain_conversation_bypasses_action_protocol_probe(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn(
            "detect_action and not report_generation and is_direct_desktop_intent(text)",
            source,
        )
        self.assertIn(
            "not DIRECT_OPENCLAW_EXECUTION\n            and openclaw_action_candidate",
            source,
        )

    def test_research_display_can_restore_real_persisted_edition_evidence(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("function restoreRecentEditionResearchDisplay()", frontend)
        self.assertIn("organizerSnapshot?.intelligence_editions", frontend)
        self.assertIn("currentResearchSources = sources", frontend)
        self.assertIn("Latest edition evidence", frontend)


if __name__ == "__main__":
    unittest.main()
