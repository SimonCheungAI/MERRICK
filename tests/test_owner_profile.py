import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from owner_profile import configured_owner_address, identity_presentation_prompt  # noqa: E402


class OwnerProfileTests(unittest.TestCase):
    def test_uses_separate_local_addresses_for_each_language(self) -> None:
        with patch.dict(os.environ, {
            "JARVIS_OWNER_ADDRESS_EN": "captain",
            "JARVIS_OWNER_ADDRESS_ZH": "阁下",
        }, clear=False):
            self.assertEqual(configured_owner_address("en"), "captain")
            self.assertEqual(configured_owner_address("zh"), "阁下")

    def test_prompt_never_gives_a_guest_the_owner_address(self) -> None:
        self.assertIn("captain", identity_presentation_prompt(True, "captain"))
        self.assertIn("Never call", identity_presentation_prompt(False, "captain"))


if __name__ == "__main__":
    unittest.main()
