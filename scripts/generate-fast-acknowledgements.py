#!/usr/bin/env python3
"""Generate the approved English MERRICK fast-acknowledgement cache."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from tts import FAST_ACK_LINES, STEADFAST_ENGINE, _steadfast, synthesize_audio


async def generate(root: Path) -> None:
    target = root / "web" / "audio" / "steadfast"
    target.mkdir(parents=True, exist_ok=True)
    await _steadfast.prewarm()
    try:
        for kind in ("conversation", "action", "research"):
            for index, text in enumerate(FAST_ACK_LINES[(kind, "en")], start=1):
                audio = await synthesize_audio(text, language="en")
                if audio.engine != STEADFAST_ENGINE or audio.mime != "audio/wav":
                    raise RuntimeError(f"{kind} {index} did not use the approved Steadfast voice.")
                path = target / f"ack-{kind}-en-{index:02d}.wav"
                path.write_bytes(audio.data)
                print(f"generated {path.name}: {text}")
    finally:
        await _steadfast.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    asyncio.run(generate(args.root.resolve()))


if __name__ == "__main__":
    main()
