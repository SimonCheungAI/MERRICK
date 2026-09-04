from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RuntimeContractTests(unittest.TestCase):
    def test_one_canonical_contract_generates_every_connection_binding(self) -> None:
        contract_path = PROJECT_ROOT / "config" / "runtime-contract.json"
        generator = PROJECT_ROOT / "scripts" / "generate-runtime-contract.py"

        self.assertTrue(contract_path.is_file(), "the canonical runtime contract is missing")
        self.assertTrue(generator.is_file(), "the runtime contract generator is missing")

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["schemaVersion"], 1)
        self.assertEqual(
            set(contract["providers"]),
            {
                "codex",
                "claude-code",
                "openai",
                "anthropic",
                "gemini",
                "kimi",
                "deepseek",
                "custom",
            },
        )
        self.assertEqual(set(contract["localServices"]), {"backend", "openclaw"})

        completed = subprocess.run(
            [sys.executable, str(generator), "--check", str(PROJECT_ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_every_connection_consumer_uses_generated_contract_bindings(self) -> None:
        native = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        probe = (PROJECT_ROOT / "desktop" / "ProviderConnectionValidation.swift").read_text(encoding="utf-8")
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(encoding="utf-8")
        launcher = (PROJECT_ROOT / "scripts" / "openclaw-common.sh").read_text(encoding="utf-8")
        gateway_launcher = (PROJECT_ROOT / "scripts" / "run-openclaw-gateway.sh").read_text(encoding="utf-8")
        web = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        index = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        python_client = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(encoding="utf-8")
        python_server = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")

        self.assertIn("RuntimeContract.generated.swift", build)
        self.assertIn("RuntimeContract.providers", native)
        self.assertIn("RuntimeContract.backendPort", native)
        self.assertIn("RuntimeContract.providers", probe)
        self.assertNotIn('case "codex", "openai": defaultBaseURL', native)
        self.assertNotIn('case "openai": environment["OPENAI_API_KEY"]', native)

        self.assertIn('. "$(dirname -- "$0")/runtime-contract.generated.sh"', launcher)
        self.assertIn("merrick_apply_provider_contract", launcher)
        self.assertNotIn('case "$JARVIS_SELECTED_PROVIDER" in', launcher)
        self.assertIn("OPENCLAW_DEFAULT_PORT", gateway_launcher)

        self.assertLess(index.index("runtime-contract.generated.js"), index.index("app.js"))
        self.assertIn("MERRICK_RUNTIME_CONTRACT.providers", web)
        self.assertIn("MERRICK_RUNTIME_CONTRACT.connectionFailures", web)
        self.assertNotIn("const PROVIDERS = {", web)

        self.assertIn("from runtime_contract_generated import CONNECTION_FAILURES", python_client)
        self.assertIn("from runtime_contract_generated import", python_server)
        self.assertIn("LOCAL_SERVICES", python_server)
        self.assertNotIn('"http://127.0.0.1:8765"', python_server)

    def test_probe_and_runtime_failures_share_one_ordered_matcher_contract(self) -> None:
        contract = json.loads(
            (PROJECT_ROOT / "config" / "runtime-contract.json").read_text(encoding="utf-8")
        )
        probe = (PROJECT_ROOT / "desktop" / "ProviderConnectionValidation.swift").read_text(
            encoding="utf-8"
        )
        runtime = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )

        self.assertGreaterEqual(len(contract["failureMatchers"]), 6)
        self.assertIn("RuntimeContract.failureMatchers", probe)
        self.assertIn("FAILURE_MATCHERS", runtime)
        self.assertNotIn('detail.contains("401")', probe)
        self.assertNotIn('"unknown model" in normalized', runtime)


if __name__ == "__main__":
    unittest.main()
