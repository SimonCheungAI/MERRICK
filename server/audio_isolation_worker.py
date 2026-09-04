"""Local WebRTC AEC3 worker for the native microphone path.

The worker accepts newline-delimited JSON on stdin.  Audio is 48 kHz mono
signed 16-bit PCM encoded as base64.  `far` frames are computer playback
reference only; `near` frames return a cleaned microphone frame.  Nothing is
written to disk or sent off-device.
"""

from __future__ import annotations

import base64
import json
import math
import sys
from collections import deque

import numpy as np
from pywebrtc_audio import AudioProcessor


SAMPLE_RATE = 48_000
MAX_REFERENCE_SAMPLES = SAMPLE_RATE * 3
MIN_PLAYBACK_RMS = 500.0
MIN_ECHO_NEAR_RMS = 180.0
MAX_RESIDUAL_RMS = 260.0
MAX_RESIDUAL_RATIO = 0.24
MAX_RESIDUAL_SPEECH_PROBABILITY = 0.35
MIN_DOUBLE_TALK_PLAYBACK_RMS = 500.0
MIN_DOUBLE_TALK_SPEECH_PROBABILITY = 0.36
MIN_DOUBLE_TALK_NEAR_TO_FAR_RATIO = 0.25
MIN_EXTERNAL_DOUBLE_TALK_NEAR_TO_FAR_RATIO = 0.17
TARGET_DOUBLE_TALK_RMS = 700.0
MAX_DOUBLE_TALK_GAIN = 8.0
MAX_DOUBLE_TALK_SOURCE_RMS = 500.0
DOUBLE_TALK_NEAR_DETAIL_MIX = 0.45


def decode_pcm(value: object) -> np.ndarray:
    if not isinstance(value, str):
        return np.empty(0, dtype=np.int16)
    try:
        return np.frombuffer(base64.b64decode(value, validate=True), dtype="<i2").copy()
    except (ValueError, TypeError):
        return np.empty(0, dtype=np.int16)


def encode_pcm(samples: np.ndarray) -> str:
    return base64.b64encode(samples.astype("<i2", copy=False).tobytes()).decode("ascii")


def signal_rms(samples: np.ndarray) -> float:
    if not len(samples):
        return 0.0
    return float(math.sqrt(float(np.mean(samples.astype(np.float64) ** 2))))


def restore_double_talk_level(
    cleaned: np.ndarray,
    *,
    near_samples: np.ndarray | None = None,
    preserve_near_detail: bool = False,
    assistant_audio_playing: bool = False,
    far_rms: float,
    near_rms: float,
    clean_rms: float,
    speech_probability: float,
) -> tuple[np.ndarray, bool, float]:
    """Lift only near-dominant speech that AEC reduced below ASR level."""

    near_to_far_ratio = near_rms / max(far_rms, 1.0)
    minimum_near_ratio = (
        MIN_EXTERNAL_DOUBLE_TALK_NEAR_TO_FAR_RATIO
        if preserve_near_detail
        else MIN_DOUBLE_TALK_NEAR_TO_FAR_RATIO
    )
    # Never manufacture a barge-in from MERRICK's own TTS. In the 17:36 live
    # failure, AEC had already reduced the speaker residue, but its VAD and
    # near/far ratio happened to pass the generic external-media double-talk
    # gate. Amplifying that residue to TARGET_DOUBLE_TALK_RMS made the native
    # host classify MERRICK as a clean nearby speaker and cancel its own turn.
    # Genuine speech over MERRICK remains available in the unamplified AEC
    # output; only external computer audio is eligible for this rescue gain.
    should_restore = (
        not assistant_audio_playing
        and far_rms >= MIN_DOUBLE_TALK_PLAYBACK_RMS
        and speech_probability >= MIN_DOUBLE_TALK_SPEECH_PROBABILITY
        and near_to_far_ratio >= minimum_near_ratio
        and 0.0 < clean_rms < MAX_DOUBLE_TALK_SOURCE_RMS
    )
    if not should_restore:
        return cleaned, False, 1.0
    gain = min(MAX_DOUBLE_TALK_GAIN, TARGET_DOUBLE_TALK_RMS / clean_rms)
    restored = np.clip(
        np.rint(cleaned.astype(np.float64) * gain),
        np.iinfo(np.int16).min,
        np.iinfo(np.int16).max,
    ).astype(np.int16)
    if (
        preserve_near_detail
        and near_samples is not None
        and len(near_samples) == len(restored)
    ):
        near_gain = TARGET_DOUBLE_TALK_RMS / max(near_rms, 1.0)
        near_at_target = near_samples.astype(np.float64) * near_gain
        restored = np.clip(
            np.rint(
                restored.astype(np.float64) * (1.0 - DOUBLE_TALK_NEAR_DETAIL_MIX)
                + near_at_target * DOUBLE_TALK_NEAR_DETAIL_MIX
            ),
            np.iinfo(np.int16).min,
            np.iinfo(np.int16).max,
        ).astype(np.int16)
    return restored, True, gain


def should_suppress_playback_residual(
    *,
    far_rms: float,
    near_rms: float,
    clean_rms: float,
    speech_probability: float = 0.0,
) -> bool:
    """Return true only for a strongly attenuated playback-only frame.

    AEC3 remains the primary filter. This final gate clears the quiet residue
    that speech recognizers can otherwise join into words across many frames.
    The deliberately narrow thresholds fail open for double-talk: nearby user
    speech survives because it retains materially more post-AEC energy.
    """

    clean_ratio = clean_rms / max(near_rms, 1.0)
    return (
        far_rms >= MIN_PLAYBACK_RMS
        and near_rms >= MIN_ECHO_NEAR_RMS
        and clean_rms <= MAX_RESIDUAL_RMS
        and clean_ratio <= MAX_RESIDUAL_RATIO
        and speech_probability <= MAX_RESIDUAL_SPEECH_PROBABILITY
    )


def write(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    # Keep the full WebRTC module local.  AEC cancels the known playback path;
    # NS/VAD then help decide whether a remaining frame is speech.  AGC is not
    # enabled here because macOS/Speech.framework already manages capture gain
    # and extra AGC can distort short owner-voice samples.
    processor = AudioProcessor(
        sample_rate=SAMPLE_RATE,
        num_channels=1,
        echo_cancellation=True,
        noise_suppression=True,
        high_pass_filter=True,
        auto_gain_control=False,
        ns_level=1,
        # ScreenCaptureKit's mixer latency varies with the output device and
        # macOS load.  A fixed number made the far reference consistently
        # misaligned on this Mac, so leave the delay at zero and let AEC3's
        # built-in delay estimator converge from the live signal.
        stream_delay_ms=0,
    )
    far_history: deque[np.ndarray] = deque()
    far_samples = 0

    for raw in sys.stdin:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        kind = message.get("kind")
        samples = decode_pcm(message.get("pcm"))
        if not len(samples):
            continue
        if kind == "far":
            far_history.append(samples)
            far_samples += len(samples)
            while far_samples > MAX_REFERENCE_SAMPLES and far_history:
                far_samples -= len(far_history.popleft())
            continue
        if kind == "reset":
            processor.reset()
            far_history.clear()
            far_samples = 0
            continue
        if kind != "near":
            continue

        # ScreenCaptureKit and CoreAudio can use different buffer sizes.  The
        # AEC accepts equal-length near/far frames, so use the latest playback
        # window and pad only during a quiet/no-reference transition.
        if far_history:
            far = np.concatenate(tuple(far_history))[-len(samples):]
            if len(far) < len(samples):
                far = np.pad(far, (len(samples) - len(far), 0))
        else:
            far = np.zeros(len(samples), dtype=np.int16)
        try:
            cleaned = processor.process(samples, far)
            probability = float(processor.speech_probability)
        except Exception:
            # The native host treats this as a fail-open frame, preserving the
            # existing microphone path rather than making voice control silent.
            cleaned = samples
            probability = 0.0
        far_rms = signal_rms(far)
        near_rms = signal_rms(samples)
        clean_rms = signal_rms(cleaned)
        cleaned, double_talk_restored, double_talk_gain = restore_double_talk_level(
            cleaned,
            near_samples=samples,
            preserve_near_detail=not bool(message.get("assistant_audio_playing", False)),
            assistant_audio_playing=bool(message.get("assistant_audio_playing", False)),
            far_rms=far_rms,
            near_rms=near_rms,
            clean_rms=clean_rms,
            speech_probability=probability,
        )
        if double_talk_restored:
            clean_rms = signal_rms(cleaned)
        playback_suppressed = should_suppress_playback_residual(
            far_rms=far_rms,
            near_rms=near_rms,
            clean_rms=clean_rms,
            speech_probability=probability,
        )
        if playback_suppressed:
            cleaned = np.zeros_like(cleaned)
            clean_rms = 0.0
        write({
            "kind": "near_result",
            "generation": int(message.get("generation", -1)),
            "session": int(message.get("session", -1)),
            "pcm": encode_pcm(cleaned),
            "speech_probability": round(max(0.0, min(1.0, probability)), 4),
            "playback_suppressed": playback_suppressed,
            "double_talk_restored": double_talk_restored,
            "double_talk_gain": round(double_talk_gain, 3),
            # Diagnostics only: bounded signal-energy values prove whether the
            # system reference is present and whether AEC attenuates it. No
            # words, waveform, or recording is retained or logged.
            "far_rms": round(far_rms, 2),
            "near_rms": round(near_rms, 2),
            "clean_rms": round(clean_rms, 2),
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
