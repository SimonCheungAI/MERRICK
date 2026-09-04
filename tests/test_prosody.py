import base64
import io
import math
import struct
import sys
import unittest
import wave
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from prosody import analyze_prosody_wav  # noqa: E402


def voiced_wav(*, modulated: bool) -> str:
    sample_rate = 24_000
    duration = 1.2
    samples = []
    phase = 0.0
    for index in range(round(sample_rate * duration)):
        elapsed = index / sample_rate
        frequency = 135.0
        if modulated:
            frequency += 32.0 * math.sin(2.0 * math.pi * 2.1 * elapsed)
        phase += 2.0 * math.pi * frequency / sample_rate
        samples.append(round(math.sin(phase) * 12_000))
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return base64.b64encode(output.getvalue()).decode()


class LocalProsodyAnalysisTests(unittest.TestCase):
    def test_steady_voice_reports_bounded_acoustic_delivery(self) -> None:
        cue = analyze_prosody_wav(voiced_wav(modulated=False))

        self.assertIsNotNone(cue)
        assert cue is not None
        self.assertGreater(cue.confidence, 0.5)
        self.assertAlmostEqual(cue.duration_seconds, 1.2, places=1)
        self.assertLess(cue.pitch_range_semitones, 2.0)
        self.assertEqual(cue.delivery, "steady")
        self.assertNotIn("emotion", cue.presentation_hint().casefold())

    def test_pitch_movement_is_distinguished_from_a_steady_voice(self) -> None:
        steady = analyze_prosody_wav(voiced_wav(modulated=False))
        varied = analyze_prosody_wav(voiced_wav(modulated=True))

        assert steady is not None and varied is not None
        self.assertGreater(varied.pitch_range_semitones, steady.pitch_range_semitones + 3.0)
        self.assertEqual(varied.delivery, "animated")

    def test_malformed_audio_is_ignored_without_external_fallback(self) -> None:
        self.assertIsNone(analyze_prosody_wav("not-base64"))
