#!/usr/bin/env python3
"""Fail release builds when generated runtime connection bindings drift."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def fail(message: str) -> None:
    raise SystemExit(f"Runtime connection contract failed: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-provider-bindings.py /path/to/jarvis-stark")
    root = Path(sys.argv[1]).resolve()
    contract_path = root / "config" / "runtime-contract.json"
    generator = root / "scripts" / "generate-runtime-contract.py"
    if not contract_path.is_file() or not generator.is_file():
        fail("canonical contract or generator is missing")

    generated = subprocess.run(
        [sys.executable, str(generator), "--check", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )
    if generated.returncode != 0:
        fail((generated.stderr or generated.stdout).strip())

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    providers = contract.get("providers", {})
    if not providers or "codex" not in providers or "custom" not in providers:
        fail("provider registry is incomplete")
    for provider_id, spec in providers.items():
        for field in (
            "defaultModel",
            "authMode",
            "profileAuthMode",
            "runtimeRoute",
            "probeRoute",
            "defaultBaseUrl",
            "baseUrlRequired",
            "credentialEnv",
        ):
            if field not in spec:
                fail(f"{provider_id} is missing {field}")
        if spec["baseUrlRequired"] and spec["defaultBaseUrl"]:
            fail(f"{provider_id} cannot require a custom URL and supply a default")

    config = (root / "openclaw" / "openclaw.template.json5").read_text(encoding="utf-8")
    api_routes = {
        spec["runtimeRoute"]
        for spec in providers.values()
        if spec["authMode"] == "api"
    }
    for route in api_routes:
        if f'"{route}":' not in config:
            fail(f"OpenClaw config is missing generated runtime route {route}")

    native = (root / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
    web = (root / "web" / "app.js").read_text(encoding="utf-8")
    launcher = (root / "scripts" / "openclaw-common.sh").read_text(encoding="utf-8")
    if "RuntimeContract.providers" not in native:
        fail("native host does not consume the generated registry")
    if "MERRICK_RUNTIME_CONTRACT.providers" not in web:
        fail("web UI does not consume the generated registry")
    if "merrick_apply_provider_contract" not in launcher:
        fail("gateway launcher does not consume the generated registry")

    print("Runtime connection contract verified: " + ", ".join(sorted(providers)))


if __name__ == "__main__":
    main()
