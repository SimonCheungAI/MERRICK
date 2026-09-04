"""Steadfast local speech synthesis with a bounded Edge fallback."""

import asyncio
import base64
import json
import logging
import os
import re
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import edge_tts

log = logging.getLogger("jarvis.tts")

STEADFAST_ENGINE = "steadfast"
FAST_ACK_ENGINE = "steadfast-cache"
FALLBACK_ENGINE = "edge"
SELECTED_ENGINE = os.getenv("JARVIS_TTS_ENGINE", STEADFAST_ENGINE).strip().lower()
STEADFAST_STARTUP_TIMEOUT_SECONDS = 120.0
STEADFAST_SYNTHESIS_TIMEOUT_SECONDS = 120.0
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BASE_MODEL_CACHE_NAME = "models--mlx-community--Qwen3-TTS-12Hz-1.7B-Base-8bit"
FAST_ACK_LINES = {
    ("conversation", "en"): (
        "Right.", "I'm with you, sir.", "Understood.", "I follow.",
        "That tracks.", "I see where you're going.", "Noted.", "Go on, sir.",
    ),
    ("action", "en"): (
        "Right. I'm on it, sir.", "Consider it handled.", "Already under way.",
        "Leave it with me.", "I have it.", "I'll see to it.", "On the case, sir.", "At once.",
    ),
    ("research", "en"): (
        "I'll dig into it.", "I'm checking the evidence.", "Let's see what holds up.",
        "I'll get the facts straight.", "I'm on the trail.", "I'll separate signal from noise.",
        "I'll take a proper look.", "I'm tracing it now.",
    ),
    ("conversation", "zh"): ("我在听。",),
    ("action", "zh"): ("好的，我来处理。",),
    ("research", "zh"): ("我现在查一下。",),
}
_FAST_ACK_FILES = {
    (kind, language): tuple(
        f"ack-{kind}-{language}-{index:02d}.wav"
        for index in range(1, len(lines) + 1)
    ) if language == "en" else (f"ack-{kind}-{language}.wav",)
    for (kind, language), lines in FAST_ACK_LINES.items()
}

VOICE_EN = "en-GB-RyanNeural"
# Yunxi is the most conversational male Mandarin option. Keep its prosody
# close to ordinary speech rather than the dramatic/news-like delivery of the
# other male variants.
VOICE_ZH = "zh-CN-YunxiNeural"
RATE_EN = "-8%"
PITCH_EN = "-6Hz"
RATE_ZH = "-4%"
PITCH_ZH = "+0Hz"
# Keep source gain neutral. WebKit plays at full scale through the ordinary
# macOS output device, so the system volume and mute controls remain the single
# source of truth for both Steadfast and the Edge fallback.
VOLUME = "+0%"


@dataclass(frozen=True)
class SynthesizedAudio:
    data: bytes
    mime: str
    engine: str


@dataclass(frozen=True)
class StreamedAudioChunk:
    data: bytes
    mime: str
    sample_rate: int | None = None
    channels: int | None = None


@dataclass(frozen=True)
class SteadfastResources:
    python: Path
    model: Path
    reference: Path
    english_reference: Path
    worker: Path


@lru_cache(maxsize=12)
def _read_cached_acknowledgement(
    kind: str,
    language: str,
    variant: int,
    root: Path,
) -> SynthesizedAudio | None:
    filenames = _FAST_ACK_FILES.get((kind, language))
    if not filenames:
        return None
    filename = filenames[variant % len(filenames)]
    path = root / "web" / "audio" / "steadfast" / filename
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data:
        return None
    return SynthesizedAudio(data=data, mime="audio/wav", engine=FAST_ACK_ENGINE)


def cached_acknowledgement(
    kind: str,
    language: str,
    *,
    variant: int = 0,
    root: Path = _PROJECT_ROOT,
) -> SynthesizedAudio | None:
    """Load one approved Steadfast cue without starting the TTS model.

    This synchronous path performs at most one small local file read per cue;
    later turns are served from memory. Missing assets fail silently so the
    ordinary TTS queue remains a safe fallback.
    """
    normalized_language = "zh" if language == "zh" else "en"
    return _read_cached_acknowledgement(kind, normalized_language, variant, root.resolve())


def fast_acknowledgement_line(kind: str, language: str, *, variant: int = 0) -> str:
    """Return the spoken copy paired with the selected cached acknowledgement."""
    normalized_language = "zh" if language == "zh" else "en"
    lines = FAST_ACK_LINES.get((kind, normalized_language), ())
    return lines[variant % len(lines)] if lines else ""


def _first_snapshot(cache_root: Path) -> Path | None:
    snapshots = cache_root / _BASE_MODEL_CACHE_NAME / "snapshots"
    if not snapshots.is_dir():
        return None
    return next((path for path in sorted(snapshots.iterdir()) if path.is_dir()), None)


def discover_steadfast_resources(root: Path = _PROJECT_ROOT) -> SteadfastResources | None:
    """Resolve either source-development or self-contained app resources."""
    env_python = os.getenv("JARVIS_STEADFAST_PYTHON", "").strip()
    env_model = os.getenv("JARVIS_STEADFAST_MODEL", "").strip()
    env_reference = os.getenv("JARVIS_STEADFAST_REFERENCE", "").strip()
    env_english_reference = os.getenv(
        "JARVIS_STEADFAST_ENGLISH_REFERENCE", ""
    ).strip()
    worker = root / "server" / "steadfast_tts_worker.py"

    if env_python and env_model and env_reference:
        candidate = SteadfastResources(
            Path(env_python).expanduser(),
            Path(env_model).expanduser(),
            Path(env_reference).expanduser(),
            Path(env_english_reference or env_reference).expanduser(),
            worker,
        )
        if all(path.exists() for path in candidate.__dict__.values()):
            return candidate

    bundled_cache = root / "voice-runtime" / "model-cache" / "hub"
    bundled_model = _first_snapshot(bundled_cache)
    bundled = SteadfastResources(
        root / "voice-runtime" / ".venv" / "bin" / "python",
        bundled_model or bundled_cache / "missing-model",
        root / "voice" / "steadfast-reference.wav",
        root / "voice" / "steadfast-reference-en.wav",
        worker,
    )
    if all(path.exists() for path in bundled.__dict__.values()):
        return bundled

    source_cache = root / "artifacts" / "voice-design" / "hf-cache" / "hub"
    source_model = _first_snapshot(source_cache)
    source = SteadfastResources(
        root / "artifacts" / "voice-design" / ".venv" / "bin" / "python",
        source_model or source_cache / "missing-model",
        root / "artifacts" / "voice-design" / "samples" / "01-jarvis-steadfast.wav",
        root / "artifacts" / "voice-design" / "samples" / "04-steadfast-english-identity.wav",
        worker,
    )
    if all(path.exists() for path in source.__dict__.values()):
        return source
    return None


class SteadfastSynthesizer:
    def __init__(self, root: Path = _PROJECT_ROOT):
        self.resources = discover_steadfast_resources(root)
        self.process: asyncio.subprocess.Process | None = None
        self.lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return self.resources is not None

    async def _stop_unlocked(self) -> None:
        process, self.process = self.process, None
        if process is None or process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    async def _start_unlocked(self) -> asyncio.subprocess.Process:
        if self.process is not None and self.process.returncode is None:
            return self.process
        if self.resources is None:
            raise RuntimeError("Steadfast voice resources are unavailable")
        self.process = await asyncio.create_subprocess_exec(
            str(self.resources.python),
            str(self.resources.worker),
            "--model", str(self.resources.model),
            "--reference", str(self.resources.reference),
            "--english-reference", str(self.resources.english_reference),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        process = self.process
        assert process.stdout is not None
        while True:
            line = await asyncio.wait_for(
                process.stdout.readline(), timeout=STEADFAST_STARTUP_TIMEOUT_SECONDS
            )
            if not line:
                raise RuntimeError("Steadfast worker exited during startup")
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "ready":
                return process

    async def prewarm(self) -> None:
        if not self.available:
            return
        async with self.lock:
            try:
                await self._start_unlocked()
            except BaseException:
                await self._stop_unlocked()
                raise

    async def synthesize(self, text: str, language: str) -> bytes:
        async with self.lock:
            output = Path(tempfile.gettempdir()) / f"jarvis-steadfast-{uuid4().hex}.wav"
            request_id = uuid4().hex
            try:
                process = await self._start_unlocked()
                assert process.stdin is not None and process.stdout is not None
                request = {
                    "id": request_id,
                    "text": text,
                    "language": "zh" if language == "zh" else "en",
                    "output": str(output),
                }
                process.stdin.write((json.dumps(request, ensure_ascii=False) + "\n").encode())
                await process.stdin.drain()
                while True:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=STEADFAST_SYNTHESIS_TIMEOUT_SECONDS,
                    )
                    if not line:
                        raise RuntimeError("Steadfast worker exited during synthesis")
                    try:
                        result = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if result.get("type") != "result" or result.get("id") != request_id:
                        continue
                    if not result.get("ok"):
                        raise RuntimeError(str(result.get("error", "Steadfast synthesis failed")))
                    return await asyncio.to_thread(output.read_bytes)
            except BaseException:
                await self._stop_unlocked()
                raise
            finally:
                output.unlink(missing_ok=True)

    async def stream(self, text: str, language: str) -> AsyncIterator[bytes]:
        """Yield native Qwen decoder PCM frames while the model is speaking."""
        async with self.lock:
            request_id = uuid4().hex
            try:
                process = await self._start_unlocked()
                assert process.stdin is not None and process.stdout is not None
                request = {
                    "id": request_id,
                    "text": text,
                    "language": "zh" if language == "zh" else "en",
                    "stream": True,
                }
                process.stdin.write((json.dumps(request, ensure_ascii=False) + "\n").encode())
                await process.stdin.drain()
                while True:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=STEADFAST_SYNTHESIS_TIMEOUT_SECONDS,
                    )
                    if not line:
                        raise RuntimeError("Steadfast worker exited during streaming synthesis")
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event.get("id") != request_id:
                        continue
                    if event.get("type") == "chunk":
                        data = event.get("data")
                        if not isinstance(data, str):
                            raise RuntimeError("Steadfast returned an invalid audio frame")
                        yield base64.b64decode(data, validate=True)
                        continue
                    if event.get("type") != "result":
                        continue
                    if not event.get("ok"):
                        raise RuntimeError(str(event.get("error", "Steadfast synthesis failed")))
                    return
            except BaseException:
                await self._stop_unlocked()
                raise

    async def shutdown(self) -> None:
        async with self.lock:
            await self._stop_unlocked()


_steadfast = SteadfastSynthesizer()

_MD_PATTERNS = [
    (re.compile(r"```.*?```", re.S), " "),          # code blocks
    (re.compile(r"`([^`]*)`"), r"\1"),               # inline code
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),      # images
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),   # links -> anchor text
    (re.compile(r"https?://\S+"), " "),               # bare URLs
    (re.compile(r"[*_#>|~]"), " "),                   # md symbols
    (re.compile(r"^\s*[-•]\s+", re.M), " "),          # bullets
    (re.compile(r"\s+"), " "),
]


# Every independent edge-tts request carries its own lead/trailing silence and
# restarts prosody. Stream one compact opening quickly, then synthesize the rest
# in large natural blocks instead of cutting at every comma or short sentence.
# Chinese punctuation does not require a following whitespace character.
_STRONG_END = re.compile(r"(?:[.!?;:\n]+(?=\s|$)|[。！？；：]+)")
_SOFT_END = re.compile(r"(?:[,—]+(?=\s|$)|[，、]+)")
# The opening must remain a whole, naturally punctuated clause. A slightly
# smaller first block reduces first-audio latency without splitting a word,
# comma phrase, or sentence across independent Edge TTS requests.
_FIRST_CHUNK_MIN = 30
_FIRST_CHUNK_TARGET = 64
_FIRST_CHUNK_MAX = 112
_FIRST_SHORT_SENTENCE_MIN = 12
_STREAM_BLOCK_TRIGGER = 620
_STREAM_BLOCK_MIN = 320
_STREAM_BLOCK_TARGET = 450
_STREAM_BLOCK_MAX = 560
_TAIL_SINGLE_MAX = 900
_TAIL_BLOCK_MIN = 450
_TAIL_BLOCK_TARGET = 600
_TAIL_BLOCK_MAX = 700
_CJK_RE = re.compile(r"[\u3400-\u9fff]")


def _natural_boundary(text: str, minimum: int, target: int, maximum: int) -> int | None:
    """Prefer sentence punctuation, then a nearby comma/dash boundary."""
    strong = [
        match.end()
        for match in _STRONG_END.finditer(text)
        if minimum <= match.end() <= maximum
    ]
    if strong:
        return min(strong, key=lambda value: abs(value - target))
    soft = [
        match.end()
        for match in _SOFT_END.finditer(text)
        if minimum <= match.end() <= maximum
    ]
    if soft:
        return min(soft, key=lambda value: abs(value - target))
    return None


def pop_first_speech_chunk(buf: str) -> tuple[list[str], str]:
    """Release at most one low-latency opening block from streamed text."""
    buf = buf.lstrip()
    # A natural Mandarin opening is often only four to eight characters
    # ("好的，先生。"), whereas an English sentence this short tends to sound
    # clipped. Keep the proven English threshold and lower it only for CJK.
    minimum_opening = 4 if _CJK_RE.search(buf) else _FIRST_SHORT_SENTENCE_MIN
    # Prefer the first complete short sentence over waiting for a longer second
    # sentence. This preserves Edge TTS prosody while allowing the response to
    # begin as soon as a natural opening is available.
    early_strong = [
        match.end()
        for match in _STRONG_END.finditer(buf)
        if minimum_opening <= match.end() <= _FIRST_CHUNK_TARGET
    ]
    if early_strong:
        boundary = early_strong[0]
        return [buf[:boundary].strip()], buf[boundary:].lstrip()
    boundary = _natural_boundary(
        buf, _FIRST_CHUNK_MIN, _FIRST_CHUNK_TARGET, _FIRST_CHUNK_MAX
    )
    if boundary is not None:
        return [buf[:boundary].strip()], buf[boundary:].lstrip()
    if len(buf) < _FIRST_CHUNK_MAX:
        return [], buf
    # Only a punctuation-free run reaches this fallback. Never cut a word.
    boundary = buf.rfind(" ", _FIRST_CHUNK_TARGET, _FIRST_CHUNK_MAX + 1)
    if boundary < _FIRST_CHUNK_MIN:
        boundary = buf.rfind(" ", _FIRST_CHUNK_MIN, _FIRST_CHUNK_MAX + 1)
    if boundary < _FIRST_CHUNK_MIN:
        return [], buf
    return [buf[:boundary].strip()], buf[boundary:].lstrip()


def pop_stream_speech_blocks(buf: str) -> tuple[list[str], str]:
    """Release large follow-up blocks early enough to stay ahead of playback."""
    blocks: list[str] = []
    buf = buf.lstrip()
    while len(buf) >= _STREAM_BLOCK_TRIGGER:
        boundary = _natural_boundary(
            buf, _STREAM_BLOCK_MIN, _STREAM_BLOCK_TARGET, _STREAM_BLOCK_MAX
        )
        if boundary is None:
            boundary = buf.rfind(" ", _STREAM_BLOCK_TARGET, _STREAM_BLOCK_MAX + 1)
        if boundary is None or boundary < _STREAM_BLOCK_MIN:
            boundary = buf.rfind(" ", _STREAM_BLOCK_MIN, _STREAM_BLOCK_MAX + 1)
        if boundary < _STREAM_BLOCK_MIN:
            return blocks, buf
        block = buf[:boundary].strip()
        buf = buf[boundary:].lstrip()
        if block:
            blocks.append(block)
    return blocks, buf


def split_speech_blocks(text: str) -> list[str]:
    """Split completed tail text into a few large, sentence-aware TTS blocks."""
    blocks: list[str] = []
    text = text.strip()
    while len(text) > _TAIL_SINGLE_MAX:
        # Avoid leaving a tiny final block when the tail is only just over the
        # single-request limit; otherwise prefer roughly 600-character blocks.
        target = _TAIL_BLOCK_TARGET
        if len(text) < _TAIL_BLOCK_TARGET + _TAIL_BLOCK_MIN:
            target = max(_TAIL_BLOCK_MIN, len(text) - _TAIL_BLOCK_MIN)
        boundary = _natural_boundary(
            text, _TAIL_BLOCK_MIN, target, _TAIL_BLOCK_MAX
        )
        if boundary is None:
            boundary = text.rfind(" ", _TAIL_BLOCK_MIN, _TAIL_BLOCK_MAX + 1)
            if boundary < _TAIL_BLOCK_MIN:
                boundary = text.rfind(" ", 1, _TAIL_BLOCK_MAX + 1)
            if boundary <= 0:
                boundary = _TAIL_BLOCK_MAX
        block = text[:boundary].strip()
        text = text[boundary:].lstrip()
        if block:
            blocks.append(block)
    if text:
        blocks.append(text)
    return blocks


def clean_for_speech(text: str) -> str:
    for pattern, repl in _MD_PATTERNS:
        text = pattern.sub(repl, text)
    return text.strip()


async def _synthesize_edge_stream(text: str, *, language: str = "en") -> AsyncIterator[bytes]:
    """Yield encoded audio frames as Edge returns them.

    The caller may play the first MP3 frames immediately through MediaSource,
    rather than waiting for the full spoken clause to finish synthesising.
    """
    is_chinese = language == "zh"
    communicate = edge_tts.Communicate(
        text,
        voice=VOICE_ZH if is_chinese else VOICE_EN,
        rate=RATE_ZH if is_chinese else RATE_EN,
        pitch=PITCH_ZH if is_chinese else PITCH_EN,
        volume=VOLUME,
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]


def supports_incremental_synthesis() -> bool:
    """Both native Steadfast PCM and Edge MP3 expose playable frames."""
    return True


async def synthesize_stream(
    text: str,
    *,
    language: str = "en",
) -> AsyncIterator[StreamedAudioChunk]:
    """Yield the selected identity's native frames with a bounded fallback."""
    if SELECTED_ENGINE == STEADFAST_ENGINE and _steadfast.available:
        try:
            async for data in _steadfast.stream(text, language):
                yield StreamedAudioChunk(
                    data=data,
                    mime="audio/pcm;format=s16le",
                    sample_rate=24_000,
                    channels=1,
                )
            return
        except Exception as exc:
            log.warning("Steadfast streaming failed; using Edge fallback: %s", exc)
    async for data in _synthesize_edge_stream(text, language=language):
        yield StreamedAudioChunk(data=data, mime="audio/mpeg")


async def prewarm() -> None:
    """Load Steadfast in the background, or warm the bounded Edge fallback."""
    if SELECTED_ENGINE == STEADFAST_ENGINE and _steadfast.available:
        try:
            await _steadfast.prewarm()
            return
        except Exception as exc:
            log.warning("Steadfast prewarm failed; Edge remains available: %s", exc)
    try:
        await asyncio.wait_for(edge_tts.list_voices(), timeout=8.0)
    except Exception:
        # Edge remains an optional presentation layer; a background warmup
        # must never delay app startup or prevent complete-MP3 fallback.
        return


async def synthesize_audio(text: str, *, language: str = "en") -> SynthesizedAudio:
    """Synthesize in the chosen identity, falling back without blocking a turn."""
    if SELECTED_ENGINE == STEADFAST_ENGINE and _steadfast.available:
        try:
            data = await _steadfast.synthesize(text, language)
            return SynthesizedAudio(data=data, mime="audio/wav", engine=STEADFAST_ENGINE)
        except Exception as exc:
            log.warning("Steadfast synthesis failed; using Edge fallback: %s", exc)
    data = b"".join([
        chunk async for chunk in _synthesize_edge_stream(text, language=language)
    ])
    return SynthesizedAudio(data=data, mime="audio/mpeg", engine=FALLBACK_ENGINE)


async def synthesize(text: str, *, language: str = "en") -> bytes:
    """Compatibility API for callers that only need encoded audio bytes."""
    return (await synthesize_audio(text, language=language)).data


async def shutdown() -> None:
    """Release the persistent local model worker during application shutdown."""
    await _steadfast.shutdown()
