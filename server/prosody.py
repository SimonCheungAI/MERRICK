"""Bounded, local acoustic delivery analysis for one voice turn."""

from __future__ import annotations

import base64
import binascii
import io
import math
import wave
from dataclasses import dataclass

import numpy as np


MAX_WAV_BYTES = 2_000_000
MAX_ANALYSIS_SECONDS = 8.0
MIN_PITCH_HZ = 75.0
MAX_PITCH_HZ = 350.0


@dataclass(frozen=True)
class ProsodyCue:
    delivery: str
    duration_seconds: float
    median_pitch_hz: float
    pitch_range_semitones: float
    rms_dbfs: float
    voiced_ratio: float
    confidence: float

    def presentation_hint(self) -> str:
        """Return bounded response-style guidance, never a mood diagnosis."""
        if self.delivery == "animated":
            return (
                "The user's vocal delivery had varied intonation. Respond "
                "attentively, lead with the answer, and keep the wording concise."
            )
        if self.delivery == "soft":
            return (
                "The user's vocal delivery was quiet. Use a clear, measured "
                "reply without becoming verbose."
            )
        if self.delivery == "steady":
            return (
                "The user's vocal delivery was acoustically steady. Keep the "
                "reply calm, direct, and concise."
            )
        return "Use a natural, direct, and concise spoken reply."


def _decode_pcm16_wav(encoded_wav: str) -> tuple[np.ndarray, int] | None:
    try:
        raw = base64.b64decode(encoded_wav, validate=True)
    except (binascii.Error, ValueError, TypeError):
        return None
    if not raw or len(raw) > MAX_WAV_BYTES:
        return None
    try:
        with wave.open(io.BytesIO(raw), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frame_count = min(
                source.getnframes(),
                round(sample_rate * MAX_ANALYSIS_SECONDS),
            )
            if channels not in {1, 2} or sample_width != 2 or not 8_000 <= sample_rate <= 96_000:
                return None
            frames = source.readframes(frame_count)
    except (EOFError, OSError, ValueError, wave.Error):
        return None
    samples = np.frombuffer(frames, dtype="<i2").astype(np.float32)
    if channels == 2:
        if samples.size % 2:
            samples = samples[:-1]
        samples = samples.reshape(-1, 2).mean(axis=1)
    samples /= 32768.0
    if samples.size < round(sample_rate * 0.25):
        return None
    return samples, sample_rate


def _frame_pitch_hz(frame: np.ndarray, sample_rate: int) -> tuple[float, float] | None:
    centered = frame - float(np.mean(frame))
    windowed = centered * np.hanning(centered.size)
    energy = float(np.dot(windowed, windowed))
    if energy <= 1e-6:
        return None
    fft_size = 1 << (2 * centered.size - 1).bit_length()
    spectrum = np.fft.rfft(windowed, n=fft_size)
    correlation = np.fft.irfft(spectrum * np.conjugate(spectrum), n=fft_size)
    correlation = correlation[: centered.size]
    minimum_lag = max(1, round(sample_rate / MAX_PITCH_HZ))
    maximum_lag = min(correlation.size - 1, round(sample_rate / MIN_PITCH_HZ))
    if maximum_lag <= minimum_lag or correlation[0] <= 0:
        return None
    region = correlation[minimum_lag : maximum_lag + 1]
    relative_index = int(np.argmax(region))
    lag = minimum_lag + relative_index
    strength = float(correlation[lag] / correlation[0])
    if strength < 0.28:
        return None
    return sample_rate / lag, min(1.0, max(0.0, strength))


def analyze_prosody_wav(encoded_wav: str) -> ProsodyCue | None:
    """Measure delivery locally from a bounded PCM WAV voice sample."""
    decoded = _decode_pcm16_wav(encoded_wav)
    if decoded is None:
        return None
    samples, sample_rate = decoded
    duration = samples.size / sample_rate
    rms = float(np.sqrt(np.mean(np.square(samples), dtype=np.float64)))
    if rms < 0.002:
        return None
    rms_dbfs = 20.0 * math.log10(max(rms, 1e-9))
    frame_size = max(256, round(sample_rate * 0.04))
    hop_size = max(128, round(sample_rate * 0.02))
    pitches: list[float] = []
    strengths: list[float] = []
    frame_count = 0
    for start in range(0, max(1, samples.size - frame_size + 1), hop_size):
        frame = samples[start : start + frame_size]
        if frame.size != frame_size:
            continue
        frame_count += 1
        frame_rms = float(np.sqrt(np.mean(np.square(frame), dtype=np.float64)))
        if frame_rms < 0.008:
            continue
        estimate = _frame_pitch_hz(frame, sample_rate)
        if estimate is None:
            continue
        pitch, strength = estimate
        pitches.append(pitch)
        strengths.append(strength)
    if len(pitches) < 5 or frame_count == 0:
        return None
    pitch_values = np.asarray(pitches, dtype=np.float64)
    semitones = 12.0 * np.log2(pitch_values / 440.0) + 69.0
    pitch_range = float(np.percentile(semitones, 90) - np.percentile(semitones, 10))
    voiced_ratio = len(pitches) / frame_count
    confidence = min(
        1.0,
        (len(pitches) / 12.0)
        * float(np.mean(strengths))
        * min(1.0, duration / 0.8),
    )
    if rms_dbfs < -32.0:
        delivery = "soft"
    elif pitch_range < 2.0:
        delivery = "steady"
    elif pitch_range >= 4.0:
        delivery = "animated"
    else:
        delivery = "natural"
    return ProsodyCue(
        delivery=delivery,
        duration_seconds=round(duration, 3),
        median_pitch_hz=round(float(np.median(pitch_values)), 2),
        pitch_range_semitones=round(pitch_range, 2),
        rms_dbfs=round(rms_dbfs, 2),
        voiced_ratio=round(voiced_ratio, 3),
        confidence=round(confidence, 3),
    )
