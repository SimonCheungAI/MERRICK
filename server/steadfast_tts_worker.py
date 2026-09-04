"""Persistent MLX worker for the selected local Steadfast voice.

The web backend intentionally runs on a small general-purpose Python runtime.
MLX Audio and its model live in an isolated Python 3.12 environment, so this
JSON-lines worker keeps the large model loaded without coupling either runtime
to the other.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
import sys
import wave
from pathlib import Path


PROTOCOL_VERSION = 1
SAMPLE_RATE = 24_000
SEED = 8210
TEMPERATURE = 0.74
TOP_K = 38
TOP_P = 0.92
REPETITION_PENALTY = 1.15
TARGET_RMS = 0.072
LEADING_SILENCE_SECONDS = 0.08
TRAILING_SILENCE_SECONDS = 0.35
STREAMING_INTERVAL_SECONDS = 0.48
STREAM_BOUNDARY_SMOOTH_SECONDS = 0.006
STREAM_HEADROOM = 0.98


def emit(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def normalise_and_pad(audio):
    """Match the approved samples' level and preserve their natural onset."""
    import numpy as np

    samples = np.asarray(audio, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        raise ValueError("The model returned empty audio")

    active = np.flatnonzero(np.abs(samples) >= 0.006)
    if active.size:
        natural_lead = int(SAMPLE_RATE * LEADING_SILENCE_SECONDS)
        start = max(0, int(active[0]) - natural_lead)
        end = int(active[-1]) + 1
        samples = samples[start:end]

    rms = float(np.sqrt(np.mean(np.square(samples), dtype=np.float64)))
    if rms > 1e-6:
        samples = samples * (TARGET_RMS / rms)
    peak = float(np.max(np.abs(samples)))
    if peak > 0.94:
        samples = samples * (0.94 / peak)

    leading = np.zeros(int(SAMPLE_RATE * LEADING_SILENCE_SECONDS), dtype=np.float32)
    trailing = np.zeros(int(SAMPLE_RATE * TRAILING_SILENCE_SECONDS), dtype=np.float32)
    return np.concatenate((leading, samples, trailing))


def write_pcm_wav(path: Path, audio) -> None:
    import numpy as np

    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())


class StreamingAudioNormalizer:
    """Preserve native level and remove discontinuities between PCM chunks."""

    def __init__(self) -> None:
        self.started = False
        self.previous_sample: float | None = None

    def encode(self, audio) -> bytes:
        import numpy as np

        samples = np.asarray(audio, dtype=np.float32).reshape(-1)
        if samples.size == 0:
            return b""
        if not self.started:
            active = np.flatnonzero(np.abs(samples) >= 0.006)
            if active.size:
                natural_lead = int(SAMPLE_RATE * LEADING_SILENCE_SECONDS)
                samples = samples[max(0, int(active[0]) - natural_lead):]
            samples = np.concatenate((
                np.zeros(int(SAMPLE_RATE * LEADING_SILENCE_SECONDS), dtype=np.float32),
                samples,
            ))
            self.started = True
        elif self.previous_sample is not None:
            transition = min(
                samples.size,
                int(SAMPLE_RATE * STREAM_BOUNDARY_SMOOTH_SECONDS),
            )
            if transition:
                correction = np.linspace(
                    self.previous_sample - float(samples[0]),
                    0.0,
                    transition,
                    dtype=np.float32,
                )
                samples[:transition] += correction
        samples = np.clip(samples, -STREAM_HEADROOM, STREAM_HEADROOM)
        self.previous_sample = float(samples[-1])
        return (samples * 32767.0).astype("<i2").tobytes()

    def trailing_silence(self) -> bytes:
        import numpy as np

        silence = np.zeros(
            int(SAMPLE_RATE * TRAILING_SILENCE_SECONDS), dtype=np.float32
        )
        if self.previous_sample is not None:
            transition = min(
                silence.size,
                int(SAMPLE_RATE * STREAM_BOUNDARY_SMOOTH_SECONDS),
            )
            silence[:transition] = np.linspace(
                self.previous_sample,
                0.0,
                transition,
                dtype=np.float32,
            )
        self.previous_sample = 0.0
        return (silence * 32767.0).astype("<i2").tobytes()


def voice_reference_for_language(
    language: str,
    *,
    mandarin_reference: Path,
    english_reference: Path,
) -> Path:
    """Keep one Steadfast identity while anchoring each language's accent."""
    return mandarin_reference if language == "zh" else english_reference


def run(
    model_path: Path,
    reference_path: Path,
    english_reference_path: Path,
) -> None:
    # Third-party loaders occasionally print progress to stdout. Keep stdout a
    # clean protocol channel and send their diagnostics to stderr instead.
    with contextlib.redirect_stdout(sys.stderr):
        import mlx.core as mx
        import numpy as np
        from mlx_audio.tts.utils import load_model

        model = load_model(str(model_path))

    emit({"type": "ready", "protocol": PROTOCOL_VERSION})
    for line in sys.stdin:
        request_id = ""
        try:
            request = json.loads(line)
            request_id = str(request.get("id", ""))
            text = str(request.get("text", "")).strip()
            is_chinese = request.get("language") == "zh"
            language = "Chinese" if is_chinese else "English"
            voice_reference = voice_reference_for_language(
                "zh" if is_chinese else "en",
                mandarin_reference=reference_path,
                english_reference=english_reference_path,
            )
            output_value = str(request.get("output", ""))
            output_path = Path(output_value).resolve() if output_value else None
            stream = request.get("stream") is True
            if not request_id or not text or (not stream and output_path is None):
                raise ValueError("Incomplete synthesis request")

            with contextlib.redirect_stdout(sys.stderr):
                mx.random.seed(SEED)
                generated = model.generate(
                    text=text,
                    ref_audio=str(voice_reference),
                    ref_text=None,
                    lang_code=language,
                    temperature=TEMPERATURE,
                    top_k=TOP_K,
                    top_p=TOP_P,
                    repetition_penalty=REPETITION_PENALTY,
                    max_tokens=2048,
                    split_pattern=None,
                    verbose=False,
                    stream=stream,
                    streaming_interval=STREAMING_INTERVAL_SECONDS,
                )
            if stream:
                normalizer = StreamingAudioNormalizer()
                chunk_count = 0
                while True:
                    try:
                        with contextlib.redirect_stdout(sys.stderr):
                            result = next(generated)
                    except StopIteration:
                        break
                    pcm = normalizer.encode(np.asarray(result.audio))
                    if not pcm:
                        continue
                    chunk_count += 1
                    emit({
                        "type": "chunk",
                        "id": request_id,
                        "data": base64.b64encode(pcm).decode("ascii"),
                        "sample_rate": SAMPLE_RATE,
                        "channels": 1,
                    })
                if not chunk_count:
                    raise ValueError("The model returned no audio")
                emit({
                    "type": "chunk",
                    "id": request_id,
                    "data": base64.b64encode(normalizer.trailing_silence()).decode("ascii"),
                    "sample_rate": SAMPLE_RATE,
                    "channels": 1,
                })
            else:
                with contextlib.redirect_stdout(sys.stderr):
                    chunks = [np.asarray(result.audio) for result in generated]
            if not stream:
                if not chunks:
                    raise ValueError("The model returned no audio")
                assert output_path is not None
                write_pcm_wav(output_path, normalise_and_pad(np.concatenate(chunks)))
            emit({"type": "result", "id": request_id, "ok": True})
        except Exception as exc:
            emit({
                "type": "result",
                "id": request_id,
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--english-reference", type=Path, required=True)
    args = parser.parse_args()
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    run(
        args.model.resolve(),
        args.reference.resolve(),
        args.english_reference.resolve(),
    )


if __name__ == "__main__":
    main()
