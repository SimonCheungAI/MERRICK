#!/usr/bin/env python3
"""Import local, manually recorded owner voice samples into MERRICK

Pass up to ten representative 16 kHz mono PCM WAV recordings. The script stores
only embeddings in MERRICK's private state directory; it never retains audio.
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from openclaw_client import gateway  # noqa: E402
from voice_identity import OwnerVoiceVerifier  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", nargs="*", type=Path, help="Local WAV recordings")
    parser.add_argument(
        "--undo-last",
        action="store_true",
        help="Remove the most recently imported local embedding.",
    )
    args = parser.parse_args()
    verifier = OwnerVoiceVerifier(gateway.state_dir)
    if args.undo_last:
        if args.samples:
            parser.error("--undo-last cannot be combined with recordings")
        print(f"Voice profile now contains {verifier.discard_last_enrollment()}/10 samples.")
        return 0
    if not args.samples:
        parser.error("provide one or more recordings, or use --undo-last")
    for path in args.samples:
        try:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            count = verifier.enroll(encoded)
        except (OSError, ValueError) as exc:
            print(f"Could not import {path}: {exc}", file=sys.stderr)
            return 1
        print(f"Imported local sample {count}/10.")
    print("Only voice embeddings were saved. Remove the temporary recordings when finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
