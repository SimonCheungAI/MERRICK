from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from local_memory import LocalMemoryStore  # noqa: E402


class LocalMemoryCandidateTests(unittest.TestCase):
    def test_everyday_like_becomes_an_unconfirmed_local_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = LocalMemoryStore(Path(temporary))
            episode_id = store.record_episode("I love jazz and quiet cafés.", "Noted.")
            self.assertIsNotNone(episode_id)
            store.consolidate_episode(int(episode_id))
            self.assertEqual(store.preference_candidates(), ["I love jazz and quiet cafés."])

    def test_episodic_continuity_recalls_only_a_relevant_older_topic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = LocalMemoryStore(Path(temporary))
            store.record_episode(
                "We decided the Atlas rollout should begin with the London team.",
                "London will be the pilot and we will review adoption after two weeks.",
            )
            store.record_episode(
                "Help me choose a birthday cake.",
                "Chocolate is the safer choice.",
            )

            relevant = store.search_continuity(
                "How should we continue the Atlas rollout?",
                limit=2,
            )
            unrelated = store.search_continuity("Tell me a joke.", limit=2)

            self.assertEqual(len(relevant), 1)
            self.assertIn("Atlas rollout", relevant[0].user_text)
            self.assertEqual(unrelated, [])

    def test_episodic_continuity_does_not_duplicate_working_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = LocalMemoryStore(Path(temporary))
            recent = (
                "We selected the Atlas laptop.",
                "Atlas is the lighter option.",
            )
            store.record_episode(*recent)

            hits = store.search_continuity(
                "What about the Atlas laptop?",
                exclude_turns=(recent,),
            )

            self.assertEqual(hits, [])

    def test_repeated_preference_evidence_promotes_to_proposed_not_active(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = LocalMemoryStore(Path(temporary))

            first_stage = store.record_preference_candidate(
                "preference.response_style",
                "Keep technical explanations detailed.",
            )
            store.record_preference_candidate(
                "preference.response_style",
                "Keep technical explanations detailed.",
            )
            third_stage = store.record_preference_candidate(
                "preference.response_style",
                "Keep technical explanations detailed.",
            )
            records = store.preference_lifecycle("preference.response_style")

            self.assertEqual(first_stage, "candidate")
            self.assertEqual(third_stage, "proposed")
            self.assertEqual(records[0]["stage"], "proposed")
            self.assertEqual(records[0]["evidence_count"], 3)
            self.assertNotEqual(records[0]["stage"], "active")

    def test_activating_latest_preference_supersedes_old_value_and_forget_removes_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = LocalMemoryStore(Path(temporary))
            store.activate_preference(
                "preference.response_style",
                "Keep replies concise.",
                revision_id="revision-one",
            )

            store.activate_preference(
                "preference.response_style",
                "Keep technical explanations detailed.",
                revision_id="revision-two",
            )
            records = store.preference_lifecycle("preference.response_style")

            self.assertEqual(
                [record["value"] for record in records if record["stage"] == "active"],
                ["Keep technical explanations detailed."],
            )
            self.assertEqual(
                [record["value"] for record in records if record["stage"] == "superseded"],
                ["Keep replies concise."],
            )

            store.forget_preference("preference.response_style")

            self.assertEqual(store.preference_lifecycle("preference.response_style"), [])


if __name__ == "__main__":
    unittest.main()
