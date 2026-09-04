#!/usr/bin/env python3
"""Developer ID signing for MERRICK's bundled native runtimes."""

from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import plistlib
import struct
import subprocess
import sys
import tempfile


def macho_type(stream) -> int | None:
    header = stream.read(16)
    if len(header) < 16:
        return None
    magic = header[:4]
    if magic in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        # Universal header: inspect the first architecture's Mach-O header.
        count = struct.unpack(">I", header[4:8])[0]
        if not 1 <= count <= 32:
            return None
        stream.seek(16)
        size = 8 if magic[-1] == 0xBF else 4
        raw_offset = stream.read(size)
        if len(raw_offset) != size:
            return None
        stream.seek(int.from_bytes(raw_offset, "big"))
        return macho_type(stream)
    endian = {b"\xcf\xfa\xed\xfe": "<", b"\xce\xfa\xed\xfe": "<",
              b"\xfe\xed\xfa\xcf": ">", b"\xfe\xed\xfa\xce": ">"}.get(magic)
    if not endian:
        return None
    kind = struct.unpack(endian + "I", header[12:16])[0]
    return kind if kind in (2, 6, 8) else None


def release_entitlements(path: Path, existing: dict) -> dict:
    if path.name in {"MERRICK.app", "MERRICK.app.building"}:
        return {
            "com.apple.security.device.audio-input": True,
            "com.apple.security.automation.apple-events": True,
        }
    if path.name in {"python3.12", "python3.14"}:
        return {
            "com.apple.security.device.audio-input": True,
            "com.apple.security.cs.disable-library-validation": True,
        }
    if path.name == "node":
        return {
            "com.apple.security.cs.allow-jit": True,
            "com.apple.security.cs.disable-library-validation": True,
        }
    return {key: value for key, value in existing.items() if key != "com.apple.security.get-task-allow"}


def sign_command(path: Path, identity: str, entitlements: Path | None = None) -> list[str]:
    command = ["/usr/bin/codesign", "--force", "--options", "runtime", "--timestamp", "--sign", identity]
    if entitlements:
        command.extend(["--entitlements", str(entitlements)])
    return command + [str(path)]


def signing_order(root: Path, binaries: list[Path], vendor_bundles: list[Path]) -> list[Path]:
    main = root / "Contents/MacOS/Merrick"
    own_code = [p for p in binaries if p != main and not any(p.is_relative_to(v) for v in vendor_bundles)]
    return sorted(own_code, key=lambda p: (-len(p.parts), str(p))) + [root]


def can_preserve(info: str, entitlements: dict, *, valid: bool, executable: bool) -> bool:
    return (valid and "Authority=Developer ID Application:" in info and "Timestamp=" in info
            and (not executable or "(runtime)" in info)
            and not entitlements.get("com.apple.security.get-task-allow"))


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, text=True, capture_output=True, timeout=180)


def signature(path: Path) -> tuple[str, dict, bool]:
    details = run(["/usr/bin/codesign", "-d", "--verbose=4", "--entitlements", ":-", str(path)])
    start = details.stdout.find("<?xml")
    entitlements = plistlib.loads(details.stdout[start:].encode()) if start >= 0 else {}
    looks_signed = "Authority=Developer ID Application:" in details.stderr
    valid = looks_signed and run([
        "/usr/bin/codesign", "--verify", "--deep", "--strict", "-R", "=anchor apple generic", str(path),
    ]).returncode == 0
    return details.stderr, entitlements, valid


def scan_native_code(root: Path) -> tuple[dict[Path, int], list[Path]]:
    native = {}
    bundles = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            path = Path(directory) / name
            if not path.is_symlink() and path.suffix in {".app", ".xpc", ".framework"}:
                bundles.append(path)
        for name in files:
            path = Path(directory) / name
            if name.endswith(".cstemp"):
                raise RuntimeError(f"Interrupted codesign temporary file must be removed from the staging copy: {path}")
            if path.is_symlink():
                continue
            with path.open("rb") as source:
                kind = macho_type(source)
            if kind:
                native[path] = kind
    return native, bundles


def signing_plan(root: Path, workers: int) -> dict:
    native, bundles = scan_native_code(root)
    # Never replace a third-party bundle's team or restricted entitlements.
    vendor_roots = [p for p in bundles if not any(p != other and p.is_relative_to(other) for other in bundles)]
    for vendor in vendor_roots:
        info, rights, valid = signature(vendor)
        if not can_preserve(info, rights, valid=valid, executable=True):
            raise RuntimeError(f"Nested vendor bundle is not release-signed; repair it upstream: {vendor}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        states = dict(zip(native, pool.map(signature, native)))
    for path, kind in native.items():
        if any(path.is_relative_to(vendor) for vendor in vendor_roots):
            info, rights, valid = states[path]
            if not can_preserve(info, rights, valid=valid, executable=kind == 2):
                raise RuntimeError(f"Vendor component is not notarization-ready: {path}")

    items = []
    for path in signing_order(root, list(native), vendor_roots):
        info, rights, valid = states.get(path, ("", {}, False))
        preserved = path != root and can_preserve(info, rights, valid=valid, executable=native[path] == 2)
        if not preserved and path != root and any(key in rights for key in (
            "com.apple.application-identifier", "com.apple.developer.team-identifier", "keychain-access-groups",
        )):
            raise RuntimeError(f"Cannot reassign vendor-specific entitlements to MERRICK: {path}")
        entitlements = release_entitlements(path, rights) if path == root or native[path] == 2 else {}
        items.append({"path": str(path), "action": "preserve" if preserved else "sign", "entitlements": entitlements})
    return {"status": "planned", "app": str(root), "native_count": len(native),
            "preserved_bundles": [str(p) for p in vendor_roots], "items": items}


def execute_plan(report: dict, identity: str, workers: int) -> None:
    def sign_item(item: dict) -> None:
        if item["action"] == "preserve":
            return
        path = Path(item["path"])
        with tempfile.TemporaryDirectory(prefix="merrick-sign-entitlements-") as directory:
            rights = Path(directory) / "entitlements.plist"
            rights.write_bytes(plistlib.dumps(item["entitlements"]))
            result = run(sign_command(path, identity, rights if item["entitlements"] else None))
            if result.returncode:
                raise RuntimeError(f"Signing failed for {path}: {result.stderr.strip()}")
        result = run(["/usr/bin/codesign", "--verify", "--strict", str(path)])
        if result.returncode:
            raise RuntimeError(f"Signature verification failed for {path}: {result.stderr.strip()}")

    # Keep private-key use serial: parallel codesign processes can stack
    # Keychain consent dialogs before the first approval has been recorded.
    # Only the read-only metadata scan uses the workers setting.
    for count, item in enumerate(report["items"][:-1], 1):
        sign_item(item)
        if count % 25 == 0:
            print(f"Verified {count}/{len(report['items']) - 1} signing targets", flush=True)
    sign_item(report["items"][-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.app.resolve()
    if root.name not in {"MERRICK.app", "MERRICK.app.building"} or not (root / "Contents/MacOS/Merrick").is_file():
        parser.error("Expected a built MERRICK.app or MERRICK.app.building with its native executable")
    if not args.identity.startswith("Developer ID Application:"):
        parser.error("Public release requires a Developer ID Application identity, never ad hoc")
    report = signing_plan(root, args.workers)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Planned {report['native_count']} native files; preserved {len(report['preserved_bundles'])} vendor bundles", flush=True)
    if not args.dry_run:
        execute_plan(report, args.identity, args.workers)
        report["status"] = "signed-and-verified"
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Developer ID signing complete: {root}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
