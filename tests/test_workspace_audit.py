from pathlib import Path
import tempfile
import unittest

from workspace_audit import WorkspaceMutationAudit


class WorkspaceMutationAuditTests(unittest.TestCase):
    def test_records_before_and_after_hashes_for_a_text_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            note = root / "note.md"
            note.write_text("before\n", encoding="utf-8")
            audit = WorkspaceMutationAudit(root, state_root=Path(temporary) / "state")

            audit.begin(turn_id="turn-42", request_text="Update the note")
            note.write_text("after\n", encoding="utf-8")
            records = audit.finish()

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["operation"], "update")
            self.assertEqual(records[0]["path"], "note.md")
            self.assertTrue(records[0]["before_hash"])
            self.assertTrue(records[0]["after_hash"])
            self.assertNotEqual(records[0]["before_hash"], records[0]["after_hash"])

    def test_refuses_to_record_paths_outside_the_authorized_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            audit = WorkspaceMutationAudit(root, state_root=Path(temporary) / "state")

            audit.begin(turn_id="turn-43", request_text="Nothing")
            records = audit.finish()

            self.assertEqual(records, [])
