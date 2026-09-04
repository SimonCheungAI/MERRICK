import json
import os
from pathlib import Path
import subprocess
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NODE = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
BRIDGE = PROJECT_ROOT / "openclaw/gateway-client-bridge/index.mjs"


class GatewayClientBridgeTests(unittest.TestCase):
    def test_bridge_uses_official_v4_client_without_a_method_allowlist(self) -> None:
        package = json.loads((PROJECT_ROOT / "package.json").read_text(encoding="utf-8"))
        source = BRIDGE.read_text(encoding="utf-8")

        self.assertEqual(package["dependencies"]["@openclaw/gateway-client"], "2026.8.1")
        self.assertEqual(package["dependencies"]["@openclaw/gateway-protocol"], "2026.8.1")
        self.assertIn('import { GatewayClient } from "@openclaw/gateway-client"', source)
        self.assertIn('import { PROTOCOL_VERSION } from "@openclaw/gateway-protocol/version"', source)
        self.assertIn("minProtocol: PROTOCOL_VERSION", source)
        self.assertIn("maxProtocol: PROTOCOL_VERSION", source)
        self.assertIn('client.request(message.method, message.params ?? {})', source)
        self.assertIn('...(details !== undefined ? { details } : {})', source)
        self.assertNotIn("ALLOWED_METHODS", source)
        for scope in (
            "operator.read",
            "operator.write",
            "operator.admin",
            "operator.approvals",
            "operator.pairing",
            "operator.questions",
            "operator.talk",
        ):
            self.assertIn(f'"{scope}"', source)

    @unittest.skipUnless(NODE.is_file(), "bundled Node runtime is unavailable")
    def test_bridge_rejects_non_loopback_gateway_before_sending_credentials(self) -> None:
        environment = os.environ.copy()
        environment["OPENCLAW_GATEWAY_URL"] = "ws://example.com:18789"
        environment["OPENCLAW_GATEWAY_TOKEN"] = "a" * 64

        result = subprocess.run(
            [str(NODE), str(BRIDGE)],
            cwd=PROJECT_ROOT,
            env=environment,
            input="",
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        payload = json.loads(result.stdout.strip())

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(payload["type"], "fatal")
        self.assertEqual(payload["code"], "NON_LOOPBACK_GATEWAY")
        self.assertNotIn(environment["OPENCLAW_GATEWAY_TOKEN"], result.stdout)
        self.assertNotIn(environment["OPENCLAW_GATEWAY_TOKEN"], result.stderr)


if __name__ == "__main__":
    unittest.main()
