import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from voice_identity import OWNER_SIMILARITY_THRESHOLD, OwnerVoiceVerifier, PROFILE_VERSION  # noqa: E402


class OwnerVoiceVerifierTests(unittest.TestCase):
    def test_discard_last_enrollment_preserves_previous_embeddings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = OwnerVoiceVerifier(Path(directory))
            verifier._write_profile({
                "version": PROFILE_VERSION,
                "anchors": [[0.0] * 256, [1.0] * 256],
                "adaptive_embeddings": [],
            })

            self.assertEqual(verifier.discard_last_enrollment(), 1)
            payload = json.loads(verifier.profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["anchors"], [[0.0] * 256])
            self.assertEqual(OWNER_SIMILARITY_THRESHOLD, 0.78)

    def test_profile_count_exposes_no_voice_vector_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = OwnerVoiceVerifier(Path(directory))
            verifier._write_profile({
                "version": PROFILE_VERSION,
                "anchors": [[0.0] * 256],
                "adaptive_embeddings": [[1.0] * 256],
            })
            self.assertEqual(verifier.profile_embedding_count(), 2)

    def test_verified_refinement_keeps_only_distinct_local_vectors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = OwnerVoiceVerifier(Path(directory))
            first = [1.0] + [0.0] * 255
            second = [0.0, 1.0] + [0.0] * 254
            verifier._write_profile({
                "version": PROFILE_VERSION,
                "anchors": [first],
                "adaptive_embeddings": [],
            })

            with patch.object(verifier, "_embed", return_value=second):
                self.assertEqual(verifier.refine_from_verified_sample("trusted"), (2, True))
                self.assertEqual(verifier.refine_from_verified_sample("trusted"), (2, False))

            payload = json.loads(verifier.profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["anchors"], [first])
            self.assertEqual(payload["adaptive_embeddings"], [second])

    def test_version_one_profile_migrates_all_existing_samples_to_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = OwnerVoiceVerifier(Path(directory))
            first = [1.0] + [0.0] * 255
            second = [0.0, 1.0] + [0.0] * 254
            verifier.profile_path.parent.mkdir(parents=True)
            verifier.profile_path.write_text(
                json.dumps({"version": 1, "embeddings": [first, second]}), encoding="utf-8"
            )

            self.assertEqual(verifier._load_embeddings(), [first, second])

    def test_adaptive_pool_never_evicts_manual_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verifier = OwnerVoiceVerifier(Path(directory))

            def basis(index: int) -> list[float]:
                values = [0.0] * 256
                values[index] = 1.0
                return values

            anchors = [basis(index) for index in range(10)]
            adaptive = [basis(index) for index in range(10, 20)]
            candidate = basis(20)
            verifier._write_profile({
                "version": PROFILE_VERSION,
                "anchors": anchors,
                "adaptive_embeddings": adaptive,
            })

            with patch.object(verifier, "_embed", return_value=candidate):
                self.assertEqual(verifier.refine_from_verified_sample("trusted"), (20, True))

            payload = json.loads(verifier.profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["anchors"], anchors)
            self.assertEqual(len(payload["adaptive_embeddings"]), 10)
            self.assertIn(candidate, payload["adaptive_embeddings"])
