import plistlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))


class MerrickBrandingTests(unittest.TestCase):
    def test_mac_app_build_and_launch_metadata_use_the_same_merrick_name(self):
        with (ROOT / "desktop" / "Info.plist").open("rb") as source:
            info = plistlib.load(source)
        build = (ROOT / "scripts" / "build-macos-app.sh").read_text()
        package = (ROOT / "scripts" / "package-macos-app.sh").read_text()

        self.assertEqual(info["CFBundleDisplayName"], "MERRICK")
        self.assertEqual(info["CFBundleName"], "MERRICK")
        self.assertEqual(info["CFBundleExecutable"], "Merrick")
        self.assertIn('dist/MERRICK.app"', build)
        self.assertIn('"$CONTENTS/MacOS/Merrick"', build)
        self.assertIn('dist/MERRICK-macOS-arm64.dmg"', package)

    def test_meeting_mode_answers_when_addressed_by_the_new_name(self):
        from main import MEETING_MERRICK_ADDRESS_RE

        self.assertIsNotNone(MEETING_MERRICK_ADDRESS_RE.match("Merrick, summarise our decisions."))
        self.assertIsNotNone(MEETING_MERRICK_ADDRESS_RE.match("Hey Merrick, what is next?"))
        self.assertIsNone(MEETING_MERRICK_ADDRESS_RE.match("Merrick's window looks different."))

    def test_native_window_and_frontend_present_the_current_identity(self):
        native = (ROOT / "desktop" / "MerrickApp.swift").read_text()
        html = (ROOT / "web" / "index.html").read_text()
        web = (ROOT / "web" / "app.js").read_text()

        self.assertTrue('window.title = "MERRICK"' in native, "Native window title must be MERRICK")
        self.assertIn('<title>MERRICK</title>', html)
        self.assertNotIn("Just A Rather Very Intelligent System", html + web)
        self.assertNotIn("J.A.R.V.I.S.", html)
        self.assertNotIn("JARVIS", html)

    def test_rename_preserves_installed_permissions_and_private_state(self):
        with (ROOT / "desktop" / "Info.plist").open("rb") as source:
            info = plistlib.load(source)
        native = (ROOT / "desktop" / "MerrickApp.swift").read_text()
        memory = (ROOT / "server" / "local_memory.py").read_text()

        self.assertEqual(info["CFBundleIdentifier"], "ai.jarvis.desktop")
        self.assertIn('"ai.jarvis.desktop.provider-credentials"', native)
        self.assertIn('"JarvisSpeechLanguage"', native)
        self.assertIn('"Library/Application Support/JarvisStark"', native)
        self.assertIn('"jarvis-memory.db"', memory)

    def test_new_and_legacy_spoken_names_still_bind_to_the_same_action(self):
        from main import has_optional_merrick_prefix
        from openclaw_client import _action_is_bound_to_utterance

        self.assertTrue(has_optional_merrick_prefix("梅里克，打开 Safari"))
        self.assertTrue(has_optional_merrick_prefix("Jarvis, open Safari"))
        self.assertTrue(_action_is_bound_to_utterance({"type": "open_app", "app": "Safari"}, "Merrick, open Safari"))
        self.assertFalse(has_optional_merrick_prefix("Merrickian open Safari"))


if __name__ == "__main__":
    unittest.main()
