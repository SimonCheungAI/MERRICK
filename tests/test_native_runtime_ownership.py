"""Run the native isolation helpers, not a Python reimplementation."""
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NativeRuntimeOwnershipTests(unittest.TestCase):
    def test_native_identity_and_inherited_environment_are_isolated(self):
        source = (ROOT / "desktop/MerrickApp.swift").read_text()
        self.assertTrue("private func merrickApplyOpenClawIsolation" in source, "Missing shared native isolation helper")
        helpers = source[source.index("private func merrickOwnsRuntimeExecutable"):source.index("/// Small local bridge")]
        with tempfile.TemporaryDirectory(prefix="merrick-native-isolation-") as directory:
            root = Path(directory).resolve()
            current = root / "current/runtime"
            current.mkdir(parents=True)
            (current / "python/bin").mkdir(parents=True)
            (current / "python/bin/python").touch()
            old = root / "Previous.app"
            external = root / "Independent.app"
            for app, identity in ((old, "ai.jarvis.desktop"), (external, "org.example.independent")):
                (app / "Contents/Resources/runtime/python/bin").mkdir(parents=True)
                (app / "Contents/Resources/runtime/python/bin/python").touch()
                with (app / "Contents/Info.plist").open("wb") as output:
                    plistlib.dump({"CFBundleIdentifier": identity, "CFBundlePackageType": "APPL"}, output)
            harness = root / "main.swift"
            harness.write_text("import Foundation\nimport Darwin\n" + helpers + f'''
precondition(merrickRuntimeExecutablePath(getpid()) != nil)
let current = {json.dumps(str(current))}
precondition(merrickOwnsRuntimeExecutable(current + "/python/bin/python", currentRuntimePath: current, bundleID: "ai.jarvis.desktop"))
precondition(!merrickOwnsRuntimeExecutable(current + "-other/python", currentRuntimePath: current, bundleID: "ai.jarvis.desktop"))
precondition(merrickOwnsRuntimeExecutable({json.dumps(str(old))} + "/Contents/Resources/runtime/python/bin/python", currentRuntimePath: current, bundleID: "ai.jarvis.desktop"))
precondition(!merrickOwnsRuntimeExecutable({json.dumps(str(external))} + "/Contents/Resources/runtime/python/bin/python", currentRuntimePath: current, bundleID: "ai.jarvis.desktop"))
var environment = ["OPENCLAW_STATE_DIR": "/independent", "OPENCLAW_CONFIG_PATH": "/independent/config", "OPENCLAW_PROFILE": "personal", "OPENCLAW_GATEWAY_TOKEN": "external-token", "OPENCLAW_TOKEN_FILE": "/independent/token", "UNRELATED_SETTING": "keep"]
merrickApplyOpenClawIsolation(&environment, stateDirectory: URL(fileURLWithPath: "/merrick/state"), workspaceDirectory: URL(fileURLWithPath: "/merrick/documents"))
precondition(environment["OPENCLAW_STATE_DIR"] == "/merrick/state")
precondition(environment["OPENCLAW_CONFIG_PATH"] == "/merrick/state/openclaw.json")
precondition(environment["OPENCLAW_TOKEN_FILE"] == "/merrick/state/.gateway-token")
precondition(environment["OPENCLAW_ACTION_SECRET_FILE"] == "/merrick/state/.action-secret")
precondition(environment["OPENCLAW_PROFILE"] == nil)
precondition(environment["OPENCLAW_GATEWAY_TOKEN"] == nil)
precondition(environment["UNRELATED_SETTING"] == "keep")
print("native-isolation-ok")
''')
            binary = root / "native-isolation-test"
            compile_result = subprocess.run(["/usr/bin/swiftc", str(harness), "-o", str(binary)], capture_output=True, text=True)
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("native-isolation-ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
