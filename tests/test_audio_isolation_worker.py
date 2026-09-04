from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from audio_isolation_worker import (
    restore_double_talk_level,
    should_suppress_playback_residual,
    signal_rms,
)


class PlaybackResidualGateTests(unittest.TestCase):
    def test_suppresses_aec_residual_dominated_by_computer_playback(self) -> None:
        self.assertTrue(
            should_suppress_playback_residual(
                far_rms=4_800.0,
                near_rms=1_260.0,
                clean_rms=101.0,
                speech_probability=0.12,
            )
        )

    def test_preserves_nearby_user_speech_during_playback(self) -> None:
        self.assertFalse(
            should_suppress_playback_residual(
                far_rms=4_800.0,
                near_rms=614.0,
                clean_rms=511.0,
                speech_probability=0.95,
            )
        )

    def test_regression_preserves_confident_user_speech_with_low_energy_ratio(self) -> None:
        # Production diagnostics showed these frames being cleared while the
        # user spoke over ongoing computer audio. WebRTC's post-AEC VAD was
        # highly confident, so an energy ratio alone must not erase the frame.
        self.assertFalse(
            should_suppress_playback_residual(
                far_rms=3_385.5,
                near_rms=2_144.1,
                clean_rms=180.0,
                speech_probability=0.90,
            )
        )

    def test_preserves_quiet_user_speech_when_computer_is_silent(self) -> None:
        self.assertFalse(
            should_suppress_playback_residual(
                far_rms=0.0,
                near_rms=190.0,
                clean_rms=145.0,
                speech_probability=0.82,
            )
        )

    def test_does_not_gate_loud_unattenuated_audio(self) -> None:
        # If AEC has not converged yet, fail open rather than accidentally
        # swallowing a user. The regular AEC path still processes the frame.
        self.assertFalse(
            should_suppress_playback_residual(
                far_rms=3_000.0,
                near_rms=1_100.0,
                clean_rms=420.0,
                speech_probability=0.80,
            )
        )

    def test_regression_restores_user_level_during_loud_computer_playback(self) -> None:
        # These are the actual diagnostics from the failed live turn: AEC
        # retained the user's speech but reduced it below a reliable ASR level.
        cleaned = np.resize(np.array([-288, 288], dtype=np.int16), 4_800)

        restored, was_restored, _ = restore_double_talk_level(
            cleaned,
            far_rms=2_233.8,
            near_rms=1_581.6,
            clean_rms=287.8,
            speech_probability=0.77,
        )

        self.assertTrue(was_restored)
        self.assertGreaterEqual(signal_rms(restored), 690.0)

    def test_regression_restores_quiet_user_without_outshouting_playback(self) -> None:
        # In the second failed live turn the user was close enough for AEC VAD
        # to detect speech, but the computer audio was much louder digitally.
        cleaned = np.resize(np.array([-102, 102], dtype=np.int16), 4_800)

        restored, was_restored, _ = restore_double_talk_level(
            cleaned,
            far_rms=6_124.6,
            near_rms=1_651.4,
            clean_rms=101.7,
            speech_probability=0.38,
        )

        self.assertTrue(was_restored)
        self.assertGreaterEqual(signal_rms(restored), 690.0)

    def test_regression_preserves_voice_detail_when_playback_is_much_louder(self) -> None:
        # Live diagnostics from the high-volume failure showed very confident
        # speech after AEC, but the playback reference still dominated the mic.
        # The cleaned waveform has lost alternating near-field detail that a
        # pure gain stage cannot recreate.
        cleaned = np.resize(np.array([-307, -307, 307, 307], dtype=np.int16), 4_800)
        near = np.resize(np.array([-895, 895, -895, 895], dtype=np.int16), 4_800)

        restored, was_restored, _ = restore_double_talk_level(
            cleaned,
            near_samples=near,
            preserve_near_detail=True,
            far_rms=4_141.9,
            near_rms=895.1,
            clean_rms=307.3,
            speech_probability=0.96,
        )

        self.assertTrue(was_restored)
        self.assertGreater(np.corrcoef(restored, near)[0, 1], 0.35)

    def test_regression_rescues_voice_when_playback_reaches_live_peak_volume(self) -> None:
        # The first 0.2.17 live probe reached this lower near/playback ratio.
        # It remains a credible double-talk frame because post-AEC VAD is over
        # 0.5, but the previous external-media threshold missed it.
        cleaned = np.resize(np.array([-112, -112, 112, 112], dtype=np.int16), 4_800)
        near = np.resize(np.array([-1_173, 1_173], dtype=np.int16), 4_800)

        _, was_restored, _ = restore_double_talk_level(
            cleaned,
            near_samples=near,
            preserve_near_detail=True,
            far_rms=6_147.9,
            near_rms=1_172.7,
            clean_rms=112.3,
            speech_probability=0.52,
        )

        self.assertTrue(was_restored)

    def test_jarvis_playback_never_mixes_raw_loudspeaker_detail_back_in(self) -> None:
        cleaned = np.resize(np.array([-307, -307, 307, 307], dtype=np.int16), 4_800)
        near = np.resize(np.array([-895, 895, -895, 895], dtype=np.int16), 4_800)

        restored, was_restored, _ = restore_double_talk_level(
            cleaned,
            near_samples=near,
            preserve_near_detail=False,
            far_rms=4_141.9,
            near_rms=895.1,
            clean_rms=307.3,
            speech_probability=0.96,
        )

        self.assertFalse(was_restored)
        self.assertEqual(signal_rms(restored), signal_rms(cleaned))

    def test_does_not_restore_loudspeaker_only_audio_with_high_vad(self) -> None:
        # The macOS Samantha end-to-end probe produced this high-VAD frame.
        # Its mic/reference ratio still identifies it as loudspeaker echo.
        cleaned = np.resize(np.array([-573, 573], dtype=np.int16), 4_800)

        restored, was_restored, gain = restore_double_talk_level(
            cleaned,
            far_rms=5_763.5,
            near_rms=2_022.6,
            clean_rms=573.4,
            speech_probability=0.99,
        )

        self.assertFalse(was_restored)
        self.assertEqual(gain, 1.0)
        self.assertEqual(signal_rms(restored), signal_rms(cleaned))

    def test_regression_jarvis_playback_is_never_promoted_into_clean_voice(self) -> None:
        """Production 17:36 metrics: gain-created 700 RMS cancelled its own turn."""
        cleaned = np.resize(np.array([-180, 180], dtype=np.int16), 4_800)

        restored, was_restored, gain = restore_double_talk_level(
            cleaned,
            assistant_audio_playing=True,
            far_rms=1_885.2,
            near_rms=756.0,
            clean_rms=180.0,
            speech_probability=0.80,
        )

        self.assertFalse(was_restored)
        self.assertEqual(gain, 1.0)
        self.assertEqual(signal_rms(restored), signal_rms(cleaned))


if __name__ == "__main__":
    unittest.main()
