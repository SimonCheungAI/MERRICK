import asyncio
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from tts import (  # noqa: E402
    FAST_ACK_ENGINE,
    VOLUME,
    RATE_ZH,
    PITCH_ZH,
    SELECTED_ENGINE,
    STEADFAST_ENGINE,
    VOICE_ZH,
    cached_acknowledgement,
    discover_steadfast_resources,
    pop_first_speech_chunk,
    supports_incremental_synthesis,
    synthesize_audio,
    synthesize_stream,
)
from steadfast_tts_worker import (  # noqa: E402
    LEADING_SILENCE_SECONDS,
    SAMPLE_RATE,
    StreamingAudioNormalizer,
    voice_reference_for_language,
)


class FirstSpeechChunkTests(unittest.TestCase):
    def test_short_complete_opening_sentence_is_released(self) -> None:
        chunk, rest = pop_first_speech_chunk(
            "Certainly, sir. I have found the relevant details."
        )
        self.assertEqual(chunk, ["Certainly, sir."])
        self.assertEqual(rest, "I have found the relevant details.")

    def test_opening_never_splits_an_unfinished_phrase(self) -> None:
        chunk, rest = pop_first_speech_chunk(
            "Certainly, sir, I will check the latest information and return with a concise answer"
        )
        self.assertEqual(chunk, [])
        self.assertIn("latest information", rest)


class StreamingSynthesisTests(unittest.TestCase):
    def test_edge_fallback_does_not_override_the_macos_output_volume(self) -> None:
        self.assertEqual(VOLUME, "+0%")

    def test_mandarin_uses_the_conversational_male_voice(self) -> None:
        self.assertEqual(VOICE_ZH, "zh-CN-YunxiNeural")
        self.assertEqual(RATE_ZH, "-4%")
        self.assertEqual(PITCH_ZH, "+0Hz")

    def test_edge_audio_frames_are_exposed_without_waiting_for_completion(self) -> None:
        class FakeCommunicate:
            async def stream(self):
                yield {"type": "WordBoundary", "data": b"ignored"}
                yield {"type": "audio", "data": b"first"}
                yield {"type": "audio", "data": b"second"}

        async def collect() -> list[bytes]:
            return [chunk async for chunk in synthesize_stream("Hello, sir.")]

        with patch("tts._steadfast.resources", None), patch(
            "tts.edge_tts.Communicate", return_value=FakeCommunicate()
        ):
            chunks = asyncio.run(collect())
        self.assertEqual([chunk.data for chunk in chunks], [b"first", b"second"])
        self.assertTrue(all(chunk.mime == "audio/mpeg" for chunk in chunks))

    def test_steadfast_exposes_native_pcm_frames_when_available(self) -> None:
        async def fake_stream(text: str, language: str):
            self.assertEqual((text, language), ("好的。", "zh"))
            yield b"pcm-one"
            yield b"pcm-two"

        async def collect():
            return [chunk async for chunk in synthesize_stream("好的。", language="zh")]

        with patch("tts._steadfast.resources", object()), patch(
            "tts._steadfast.stream", side_effect=fake_stream
        ):
            chunks = asyncio.run(collect())
            self.assertTrue(supports_incremental_synthesis())

        self.assertEqual([chunk.data for chunk in chunks], [b"pcm-one", b"pcm-two"])
        self.assertTrue(all(chunk.mime == "audio/pcm;format=s16le" for chunk in chunks))
        self.assertTrue(all(chunk.sample_rate == 24_000 for chunk in chunks))
        self.assertTrue(all(chunk.channels == 1 for chunk in chunks))


class SteadfastSynthesisTests(unittest.TestCase):
    def test_streaming_voice_uses_one_effective_gain_for_every_decoder_chunk(self) -> None:
        import numpy as np

        phase = np.linspace(0.0, np.pi * 8.0, 2_400, endpoint=False)
        quiet = (np.sin(phase) * 0.04).astype(np.float32)
        loud = (np.sin(phase) * 0.82).astype(np.float32)
        conditioner = StreamingAudioNormalizer()

        quiet_pcm = conditioner.encode(quiet)
        loud_pcm = conditioner.encode(loud)

        leading_samples = int(SAMPLE_RATE * LEADING_SILENCE_SECONDS)
        quiet_output = np.frombuffer(quiet_pcm, dtype="<i2").astype(np.float32)[
            leading_samples:
        ] / 32767.0
        loud_output = np.frombuffer(loud_pcm, dtype="<i2").astype(np.float32) / 32767.0
        quiet_gain = float(np.sqrt(np.mean(quiet_output**2))) / float(
            np.sqrt(np.mean(quiet**2))
        )
        loud_gain = float(np.sqrt(np.mean(loud_output**2))) / float(
            np.sqrt(np.mean(loud**2))
        )

        self.assertAlmostEqual(quiet_gain, loud_gain, delta=0.02)

    def test_streaming_voice_smooths_a_hard_decoder_chunk_boundary(self) -> None:
        import numpy as np

        first = np.full(2_400, 0.18, dtype=np.float32)
        second = np.full(2_400, -0.18, dtype=np.float32)
        conditioner = StreamingAudioNormalizer()

        first_pcm = conditioner.encode(first)
        second_pcm = conditioner.encode(second)

        last_sample = struct.unpack("<h", first_pcm[-2:])[0]
        first_sample = struct.unpack("<h", second_pcm[:2])[0]
        self.assertLessEqual(abs(first_sample - last_sample), 1)

    def test_streaming_voice_fades_the_final_sample_into_trailing_silence(self) -> None:
        import numpy as np

        final_chunk = np.full(2_400, 0.18, dtype=np.float32)
        conditioner = StreamingAudioNormalizer()

        final_pcm = conditioner.encode(final_chunk)
        trailing_pcm = conditioner.trailing_silence()

        last_sample = struct.unpack("<h", final_pcm[-2:])[0]
        first_silence_sample = struct.unpack("<h", trailing_pcm[:2])[0]
        self.assertLessEqual(abs(first_silence_sample - last_sample), 1)

    def test_steadfast_is_the_default_selected_identity(self) -> None:
        self.assertEqual(SELECTED_ENGINE, STEADFAST_ENGINE)

    def test_english_uses_the_steadfast_identity_calibration_reference(self) -> None:
        mandarin = Path("steadfast-reference.wav")
        english = Path("steadfast-reference-en.wav")

        selected = voice_reference_for_language(
            "en",
            mandarin_reference=mandarin,
            english_reference=english,
        )

        self.assertEqual(selected, english)

    def test_mandarin_keeps_the_original_steadfast_reference(self) -> None:
        mandarin = Path("steadfast-reference.wav")
        english = Path("steadfast-reference-en.wav")

        selected = voice_reference_for_language(
            "zh",
            mandarin_reference=mandarin,
            english_reference=english,
        )

        self.assertEqual(selected, mandarin)

    def test_source_checkout_resolves_the_approved_bilingual_identity_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = (
                root / "server" / "steadfast_tts_worker.py",
                root / "artifacts" / "voice-design" / ".venv" / "bin" / "python",
                root / "artifacts" / "voice-design" / "samples" / "01-jarvis-steadfast.wav",
                root / "artifacts" / "voice-design" / "samples" / "04-steadfast-english-identity.wav",
                root / "artifacts" / "voice-design" / "hf-cache" / "hub"
                / "models--mlx-community--Qwen3-TTS-12Hz-1.7B-Base-8bit"
                / "snapshots" / "approved" / "config.json",
            )
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            resources = discover_steadfast_resources(root)
            self.assertIsNotNone(resources)
            assert resources is not None
            self.assertEqual(resources.reference.name, "01-jarvis-steadfast.wav")
            self.assertEqual(
                resources.english_reference.name,
                "04-steadfast-english-identity.wav",
            )
            self.assertEqual(resources.worker.name, "steadfast_tts_worker.py")

    def test_steadfast_audio_is_labelled_as_wav(self) -> None:
        async def run() -> tuple[bytes, str, str]:
            with patch("tts._steadfast.resources", object()), patch(
                "tts._steadfast.synthesize", return_value=b"steadfast-wav"
            ):
                result = await synthesize_audio("好的，先生。", language="zh")
                return result.data, result.mime, result.engine

        self.assertEqual(
            asyncio.run(run()),
            (b"steadfast-wav", "audio/wav", STEADFAST_ENGINE),
        )

    def test_local_failure_falls_back_to_edge_without_holding_the_turn(self) -> None:
        class FakeCommunicate:
            async def stream(self):
                yield {"type": "audio", "data": b"edge-mp3"}

        async def run() -> tuple[bytes, str]:
            with patch("tts._steadfast.resources", object()), patch(
                "tts._steadfast.synthesize", side_effect=RuntimeError("offline")
            ), patch("tts.edge_tts.Communicate", return_value=FakeCommunicate()):
                result = await synthesize_audio("Hello, sir.", language="en")
                return result.data, result.mime

        self.assertEqual(asyncio.run(run()), (b"edge-mp3", "audio/mpeg"))


class CachedAcknowledgementTests(unittest.TestCase):
    def test_approved_acknowledgement_is_loaded_without_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "web" / "audio" / "steadfast" / "ack-action-zh.wav"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"pre-generated-steadfast")

            result = cached_acknowledgement("action", "zh", root=root)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.data, b"pre-generated-steadfast")
        self.assertEqual(result.mime, "audio/wav")
        self.assertEqual(result.engine, FAST_ACK_ENGINE)

    def test_neutral_conversation_acknowledgement_is_loaded_without_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "web" / "audio" / "steadfast" / "ack-conversation-en-01.wav"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"pre-generated-conversation-cue")

            result = cached_acknowledgement("conversation", "en", root=root)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.data, b"pre-generated-conversation-cue")
        self.assertEqual(result.mime, "audio/wav")

    def test_cached_acknowledgement_uses_the_requested_voice_variant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "web" / "audio" / "steadfast" / "ack-action-en-03.wav"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"third-voice-variant")

            result = cached_acknowledgement("action", "en", variant=2, root=root)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.data, b"third-voice-variant")

    def test_unknown_or_missing_acknowledgement_fails_silently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(cached_acknowledgement("conversation", "zh", root=root))
            self.assertIsNone(cached_acknowledgement("research", "en", root=root))


if __name__ == "__main__":
    unittest.main()
