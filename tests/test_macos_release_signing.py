import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_signer():
    spec = importlib.util.spec_from_file_location("release_signing", ROOT / "scripts/macos_release_signing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacOSReleaseSigningTests(unittest.TestCase):
    def test_public_signing_uses_hardened_runtime_without_recursive_resigning(self):
        script = ROOT / "scripts" / "macos_release_signing.py"
        self.assertTrue(script.is_file(), "A dedicated inside-out release signer is required")
        spec = importlib.util.spec_from_file_location("release_signing", script)
        signer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(signer)

        command = signer.sign_command(Path("MERRICK.app"), "Developer ID Application: Test")

        self.assertIn("--timestamp", command)
        self.assertIn("runtime", command)
        self.assertNotIn("--deep", command)
        self.assertNotIn("--requirements", command)

    def test_node_release_removes_debug_permissions_but_retains_jit_and_plugin_loading(self):
        signer = load_signer()
        original = {"com.apple.security.get-task-allow": True}

        entitlements = signer.release_entitlements(Path("Contents/Resources/runtime/node/bin/node"), original)

        self.assertEqual(entitlements, {
            "com.apple.security.cs.allow-jit": True,
            "com.apple.security.cs.disable-library-validation": True,
        })
        self.assertEqual(original, {"com.apple.security.get-task-allow": True})

    def test_native_app_and_python_retain_the_resources_needed_by_voice_and_automation(self):
        signer = load_signer()

        app = signer.release_entitlements(Path("MERRICK.app"), {})
        python = signer.release_entitlements(Path("runtime/voice-runtime/python/bin/python3.12"), {})

        self.assertEqual(app, {
            "com.apple.security.device.audio-input": True,
            "com.apple.security.automation.apple-events": True,
        })
        self.assertEqual(signer.release_entitlements(Path("MERRICK.app.building"), {}), app)
        self.assertEqual(python, {
            "com.apple.security.device.audio-input": True,
            "com.apple.security.cs.disable-library-validation": True,
        })
        self.assertEqual(signer.release_entitlements(Path("helper"), {"com.apple.security.get-task-allow": True}), {})

    def test_binary_detection_covers_arm_and_universal_but_ignores_data_and_objects(self):
        signer = load_signer()
        executable = bytes.fromhex("cffaedfe") + struct.pack("<III", 0x100000C, 0, 2)
        object_file = bytes.fromhex("cffaedfe") + struct.pack("<III", 0x100000C, 0, 1)
        universal = struct.pack(">IIiiIII", 0xCAFEBABE, 1, 0x100000C, 0, 32, 16, 0) + b"\0" * 4 + executable

        self.assertEqual(signer.macho_type(io.BytesIO(executable)), 2)
        self.assertEqual(signer.macho_type(io.BytesIO(universal)), 2)
        self.assertIsNone(signer.macho_type(io.BytesIO(object_file)))
        self.assertIsNone(signer.macho_type(io.BytesIO(b"ordinary resource data")))

    def test_signing_order_keeps_vendor_bundles_intact_and_signs_main_app_last(self):
        signer = load_signer()
        root = Path("/release/MERRICK.app")
        vendor = root / "Contents/Resources/Vendor.app"
        module = root / "Contents/Resources/python/lib/module.so"
        main = root / "Contents/MacOS/Merrick"
        helper = vendor / "Contents/MacOS/Vendor"

        self.assertEqual(signer.signing_order(root, [main, helper, module], [vendor]), [module, root])

    def test_only_valid_timestamped_release_signatures_can_be_preserved(self):
        signer = load_signer()
        info = "Authority=Developer ID Application: Vendor\nTimestamp=today\nflags=0x10000(runtime)"

        self.assertTrue(signer.can_preserve(info, {}, valid=True, executable=True))
        self.assertFalse(signer.can_preserve(info, {"com.apple.security.get-task-allow": True}, valid=True, executable=True))
        self.assertFalse(signer.can_preserve(info, {}, valid=False, executable=True))
        self.assertFalse(signer.can_preserve("Signature=adhoc", {}, valid=True, executable=True))
        self.assertFalse(signer.can_preserve(info.replace("Timestamp=today", ""), {}, valid=True, executable=True))

    def test_apple_trust_requirement_is_passed_as_an_inline_expression(self):
        signer = load_signer()
        commands = []

        def runner(command):
            commands.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="Authority=Developer ID Application: Vendor")

        signer.run = runner
        signer.signature(Path("Vendor.app"))

        verification = commands[-1]
        self.assertEqual(verification[verification.index("-R") + 1], "=anchor apple generic")

    def test_executor_verifies_each_leaf_before_sealing_the_app_and_never_resigns_preserved_code(self):
        signer = load_signer()
        commands = []

        def runner(command):
            commands.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        signer.run = runner
        report = {"items": [
            {"path": "/release/module.so", "action": "sign", "entitlements": {}},
            {"path": "/release/vendor", "action": "preserve", "entitlements": {}},
            {"path": "/release/MERRICK.app", "action": "sign", "entitlements": {}},
        ]}

        signer.execute_plan(report, "Developer ID Application: Test", workers=1)

        self.assertEqual([command[-1] for command in commands], [
            "/release/module.so", "/release/module.so", "/release/MERRICK.app", "/release/MERRICK.app",
        ])
        self.assertIn("--verify", commands[1])
        self.assertIn("--verify", commands[-1])

    def test_signing_never_starts_parallel_keychain_authorization_requests(self):
        signer = load_signer()
        owner_thread = threading.current_thread()

        def runner(command):
            self.assertIs(threading.current_thread(), owner_thread, "Signing must remain serial even when scanning uses workers")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        signer.run = runner
        report = {"items": [
            {"path": "/release/first.so", "action": "sign", "entitlements": {}},
            {"path": "/release/second.so", "action": "sign", "entitlements": {}},
            {"path": "/release/MERRICK.app", "action": "sign", "entitlements": {}},
        ]}

        signer.execute_plan(report, "Developer ID Application: Test", workers=4)

    def test_dry_run_finds_nested_native_code_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "MERRICK.app"
            main = root / "Contents/MacOS/Merrick"
            module = root / "Contents/Resources/runtime/module.so"
            main.parent.mkdir(parents=True)
            module.parent.mkdir(parents=True)
            executable = bytes.fromhex("cffaedfe") + struct.pack("<III", 0x100000C, 0, 2)
            library = bytes.fromhex("cffaedfe") + struct.pack("<III", 0x100000C, 0, 8)
            main.write_bytes(executable)
            module.write_bytes(library)
            (module.parent / "data.txt").write_text("not executable")
            report = Path(directory) / "report.json"

            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/macos_release_signing.py"), str(root),
                "--identity", "Developer ID Application: Test", "--dry-run", "--report", str(report),
            ], capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(report.exists(), "Dry run must emit an auditable signing plan")
            data = json.loads(report.read_text())
            self.assertEqual(data["native_count"], 2)
            self.assertEqual([item["path"] for item in data["items"]], [str(module.resolve()), str(root.resolve())])
            self.assertEqual(main.read_bytes(), executable)
            self.assertEqual(module.read_bytes(), library)

    def test_public_build_routes_through_the_audited_signer(self):
        build = (ROOT / "scripts/build-macos-app.sh").read_text()
        public_branch = build[build.index('if [[ -n "$CODESIGN_IDENTITY"'):build.index("\nelse\n", build.index('if [[ -n "$CODESIGN_IDENTITY"'))]

        self.assertIn("macos_release_signing.py", public_branch)
        self.assertNotIn("--deep", public_branch)
        self.assertNotIn("--requirements", public_branch)

    def test_interrupted_codesign_temporary_files_are_rejected_before_resuming(self):
        signer = load_signer()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "module.so.cstemp").write_bytes(b"unfinished signing output")

            with self.assertRaisesRegex(RuntimeError, "Interrupted codesign temporary file"):
                signer.scan_native_code(root)

    def test_distribution_signs_the_disk_image_and_checks_apples_accepted_status(self):
        package = (ROOT / "scripts/package-macos-app.sh").read_text()

        self.assertIn('codesign --force --timestamp --sign "$SIGN_IDENTITY" "$DMG"', package)
        self.assertIn('--output-format json', package)
        self.assertIn('notarytool log', package)
        self.assertIn('"Accepted"', package)
        self.assertLess(package.index('codesign --force --timestamp'), package.index('notarytool submit'))

    def test_runtime_verification_cannot_write_bytecode_into_the_signed_app(self):
        verifier = (ROOT / "scripts/verify-macos-release.sh").read_text()

        self.assertEqual(verifier.count('"$RUNTIME/.venv/bin/python" -I -B -c'), 2)


if __name__ == "__main__":
    unittest.main()
