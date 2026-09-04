#!/usr/bin/env python3
"""Generate language bindings from MERRICK's one runtime connection contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def canonical_json(contract: dict[str, object]) -> str:
    return json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_contract(contract: dict[str, object]) -> None:
    if contract.get("schemaVersion") != 1:
        raise SystemExit("Unsupported runtime contract schema")
    services = contract.get("localServices", {})
    if set(services) != {"backend", "openclaw"}:
        raise SystemExit("Runtime contract must define backend and openclaw services")
    ports: set[int] = set()
    for service_id, service in services.items():
        if service.get("host") != "127.0.0.1":
            raise SystemExit(f"{service_id} must remain on the IPv4 loopback host")
        port = service.get("port")
        if not isinstance(port, int) or not 1024 <= port <= 65535 or port in ports:
            raise SystemExit(f"{service_id} has an invalid or duplicate port")
        ports.add(port)
    backend = services["backend"]
    for field in ("healthPath", "websocketPath"):
        if not isinstance(backend.get(field), str) or not backend[field].startswith("/"):
            raise SystemExit(f"backend {field} must be an absolute local path")

    model_routes = contract.get("modelRoutes", {})
    providers = contract.get("providers", {})
    if not providers or not model_routes:
        raise SystemExit("Runtime contract providers or model routes are missing")
    environment_name = re.compile(r"[A-Z][A-Z0-9_]*\Z")
    for provider_id, spec in providers.items():
        if spec.get("authMode") not in {"api", "cli"}:
            raise SystemExit(f"{provider_id} has an invalid auth mode")
        route = model_routes.get(spec.get("runtimeRoute"))
        if route is None:
            raise SystemExit(f"{provider_id} references an unknown runtime route")
        expected_kind = "api" if spec["authMode"] == "api" else "agentRuntime"
        if route.get("kind") != expected_kind:
            raise SystemExit(f"{provider_id} auth mode and runtime route disagree")
        if spec.get("baseUrlRequired") and spec.get("defaultBaseUrl"):
            raise SystemExit(f"{provider_id} cannot require and default its base URL")
        if not spec.get("baseUrlRequired") and not spec.get("defaultBaseUrl"):
            raise SystemExit(f"{provider_id} must supply a base URL or require one")
        credentials = spec.get("credentialEnv", [])
        if len(credentials) != len(set(credentials)) or any(
            not environment_name.fullmatch(name) for name in credentials
        ):
            raise SystemExit(f"{provider_id} has invalid credential environment names")

    failures = contract.get("connectionFailures", {})
    matchers = contract.get("failureMatchers", [])
    if not failures or not matchers:
        raise SystemExit("Connection failure metadata or matchers are missing")
    for matcher in matchers:
        for field in ("runtimeCode", "probeCode"):
            if matcher.get(field) not in failures:
                raise SystemExit(f"Failure matcher references unknown {field}")
        try:
            re.compile(matcher["pattern"])
        except (KeyError, re.error) as exc:
            raise SystemExit("Failure matcher has an invalid regular expression") from exc


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def swift_optional(value: str | None) -> str:
    return "nil" if value is None else quoted(value)


def render_swift(contract: dict[str, object], digest: str) -> str:
    services = contract["localServices"]
    providers = contract["providers"]
    failures = contract["connectionFailures"]
    matchers = contract["failureMatchers"]
    stages = contract["connectionStages"]
    provider_rows: list[str] = []
    for provider_id, spec in providers.items():
        envs = ", ".join(quoted(item) for item in spec["credentialEnv"])
        provider_rows.append(
            f'''        {quoted(provider_id)}: ProviderContractSpec(
            id: {quoted(provider_id)}, title: {quoted(spec["title"])}, detail: {quoted(spec["detail"])},
            defaultModel: {quoted(spec["defaultModel"])}, authMode: {quoted(spec["authMode"])},
            profileAuthMode: {quoted(spec["profileAuthMode"])}, runtimeRoute: {quoted(spec["runtimeRoute"])},
            probeRoute: {quoted(spec["probeRoute"])}, probeProfileID: {swift_optional(spec["probeProfileId"])},
            defaultBaseURL: {quoted(spec["defaultBaseUrl"])}, baseURLRequired: {str(spec["baseUrlRequired"]).lower()},
            conversationModel: {swift_optional(spec["conversationModel"])},
            openAIRuntime: {quoted(spec["openaiRuntime"])}, anthropicRuntime: {quoted(spec["anthropicRuntime"])},
            credentialEnvironmentNames: [{envs}]
        ),'''
        )
    failure_rows: list[str] = []
    for code, spec in failures.items():
        failure_rows.append(
            f'''        {quoted(code)}: ConnectionFailureContractSpec(
            code: {quoted(code)}, retryable: {str(spec["retryable"]).lower()},
            reconnectRequired: {str(spec["reconnectRequired"]).lower()},
            messageEnglish: {quoted(spec["messageEn"])}, messageChinese: {quoted(spec["messageZh"])},
            shortEnglish: {quoted(spec["shortEn"])}, shortChinese: {quoted(spec["shortZh"])}
        ),'''
        )
    backend = services["backend"]
    openclaw = services["openclaw"]
    return f'''// Generated by scripts/generate-runtime-contract.py. Do not edit.
// contract-sha256: {digest}
import Foundation

enum ProviderConnectionStage: String, Codable {{
{chr(10).join(f'    case {name} = {quoted(value)}' for name, value in stages.items())}
}}

struct ProviderContractSpec {{
    let id: String
    let title: String
    let detail: String
    let defaultModel: String
    let authMode: String
    let profileAuthMode: String
    let runtimeRoute: String
    let probeRoute: String
    let probeProfileID: String?
    let defaultBaseURL: String
    let baseURLRequired: Bool
    let conversationModel: String?
    let openAIRuntime: String
    let anthropicRuntime: String
    let credentialEnvironmentNames: [String]
}}

struct ConnectionFailureContractSpec {{
    let code: String
    let retryable: Bool
    let reconnectRequired: Bool
    let messageEnglish: String
    let messageChinese: String
    let shortEnglish: String
    let shortChinese: String
}}

struct FailureMatcherContractSpec {{
    let runtimeCode: String
    let probeCode: String
    let pattern: String
}}

enum RuntimeContract {{
    static let digest = {quoted(digest)}
    static let backendHost = {quoted(backend["host"])}
    static let backendPort = {backend["port"]}
    static let backendHealthPath = {quoted(backend["healthPath"])}
    static let backendWebSocketPath = {quoted(backend["websocketPath"])}
    static let openClawHost = {quoted(openclaw["host"])}
    static let openClawDefaultPort = {openclaw["port"]}

    static let providers: [String: ProviderContractSpec] = [
{chr(10).join(provider_rows)}
    ]

    static let connectionFailures: [String: ConnectionFailureContractSpec] = [
{chr(10).join(failure_rows)}
    ]

    static let failureMatchers: [FailureMatcherContractSpec] = [
{chr(10).join(f'        FailureMatcherContractSpec(runtimeCode: {quoted(item["runtimeCode"])}, probeCode: {quoted(item["probeCode"])}, pattern: {quoted(item["pattern"])}),' for item in matchers)}
    ]

    static let defaultProvider = providers["codex"]!
}}
'''


def render_javascript(contract: dict[str, object], digest: str) -> str:
    compact = json.dumps(contract, ensure_ascii=False, sort_keys=True, indent=2)
    return f'''// Generated by scripts/generate-runtime-contract.py. Do not edit.
// contract-sha256: {digest}
globalThis.MERRICK_RUNTIME_CONTRACT = Object.freeze({compact});
'''


def render_python(contract: dict[str, object], digest: str) -> str:
    compact = json.dumps(contract, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f'''# Generated by scripts/generate-runtime-contract.py. Do not edit.
# contract-sha256: {digest}
from __future__ import annotations

import json

RUNTIME_CONTRACT = json.loads({compact!r})
LOCAL_SERVICES = RUNTIME_CONTRACT["localServices"]
PROVIDERS = RUNTIME_CONTRACT["providers"]
CONNECTION_FAILURES = RUNTIME_CONTRACT["connectionFailures"]
FAILURE_MATCHERS = RUNTIME_CONTRACT["failureMatchers"]
DEFAULT_PROVIDER_ID = "codex"
'''


def shell_value(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def render_shell(contract: dict[str, object], digest: str) -> str:
    providers = contract["providers"]
    backend = contract["localServices"]["backend"]
    openclaw = contract["localServices"]["openclaw"]
    cases: list[str] = []
    for provider_id, spec in providers.items():
        lines = [
            f"  {provider_id})",
            f'    JARVIS_MAIN_MODEL="{spec["runtimeRoute"]}/$JARVIS_SELECTED_MODEL"',
            f'    JARVIS_OPENAI_RUNTIME={shell_value(spec["openaiRuntime"])}',
            f'    JARVIS_ANTHROPIC_RUNTIME={shell_value(spec["anthropicRuntime"])}',
        ]
        if spec["conversationModel"]:
            lines.append(f'    JARVIS_CONVERSATION_MODEL={shell_value(spec["conversationModel"])}')
        if spec["defaultBaseUrl"]:
            lines.append(
                f'    : "${{JARVIS_SELECTED_BASE_URL:={spec["defaultBaseUrl"]}}}"'
            )
        if spec["baseUrlRequired"]:
            lines.extend([
                '    if [ -z "$JARVIS_SELECTED_BASE_URL" ]; then',
                '      echo "A custom provider needs an HTTPS base URL." >&2',
                '      return 1',
                '    fi',
            ])
        lines.append("    ;;")
        cases.append("\n".join(lines))
    return f'''# Generated by scripts/generate-runtime-contract.py. Do not edit.
# contract-sha256: {digest}
JARVIS_DEFAULT_PROVIDER=codex
JARVIS_DEFAULT_MODEL={shell_value(providers["codex"]["defaultModel"])}
JARVIS_DEFAULT_PROBE_ROUTE={shell_value(providers["codex"]["probeRoute"])}
JARVIS_DEFAULT_PROBE_PROFILE_ID={shell_value(providers["codex"]["probeProfileId"])}
JARVIS_BACKEND_HOST={shell_value(backend["host"])}
JARVIS_BACKEND_PORT={backend["port"]}
OPENCLAW_DEFAULT_HOST={shell_value(openclaw["host"])}
OPENCLAW_DEFAULT_PORT={openclaw["port"]}

merrick_apply_provider_contract() {{
  JARVIS_CONVERSATION_MODEL=""
  case "$JARVIS_SELECTED_PROVIDER" in
{chr(10).join(cases)}
  *)
    echo "Unsupported MERRICK provider selection." >&2
    return 1
    ;;
  esac
  JARVIS_CONVERSATION_MODEL=${{JARVIS_CONVERSATION_MODEL:-$JARVIS_MAIN_MODEL}}
}}
'''


def render_openclaw_routes(contract: dict[str, object], digest: str) -> str:
    rows = [f"      // contract-sha256: {digest}"]
    for route_id, spec in contract["modelRoutes"].items():
        rows.append(f"      {quoted(route_id)}: {{")
        if spec["kind"] == "agentRuntime":
            rows.append(
                f'        agentRuntime: {{ id: "${{{spec["runtimeEnv"]}}}" }},'
            )
        else:
            rows.extend([
                '        baseUrl: "${JARVIS_SELECTED_BASE_URL}",',
                '        apiKey: { source: "env", provider: "default", id: "JARVIS_MODEL_API_KEY" },',
                f'        api: {quoted(spec["protocol"])},',
                '        models: [',
                '          {',
                '            id: "${JARVIS_SELECTED_MODEL}",',
                f'            name: {quoted(spec["displayName"])},',
                '            input: ["text", "image"],',
                f'            contextWindow: {spec["contextWindow"]},',
                f'            maxTokens: {spec["maxTokens"]},',
                '          },',
                '        ],',
            ])
        rows.append("      },")
    return "\n".join(rows) + "\n"


def render_openclaw_template(root: Path, contract: dict[str, object], digest: str) -> str:
    path = root / "openclaw" / "openclaw.template.json5"
    source = path.read_text(encoding="utf-8")
    gateway_begin = "    // BEGIN GENERATED RUNTIME CONTRACT GATEWAY\n"
    gateway_end = "    // END GENERATED RUNTIME CONTRACT GATEWAY"
    route_begin = "      // BEGIN GENERATED RUNTIME CONTRACT MODEL ROUTES\n"
    route_end = "      // END GENERATED RUNTIME CONTRACT MODEL ROUTES"
    for marker in (gateway_begin, gateway_end, route_begin, route_end):
        if marker not in source:
            raise SystemExit(f"OpenClaw template is missing marker: {marker.strip()}")
    prefix, remainder = source.split(gateway_begin, 1)
    _, suffix = remainder.split(gateway_end, 1)
    gateway = contract["localServices"]["openclaw"]
    source = (
        prefix + gateway_begin
        + f"    // contract-sha256: {digest}\n"
        + f"    port: {gateway['port']},\n"
        + gateway_end + suffix
    )
    prefix, remainder = source.split(route_begin, 1)
    _, suffix = remainder.split(route_end, 1)
    return prefix + route_begin + render_openclaw_routes(contract, digest) + route_end + suffix


def output_files(root: Path, contract: dict[str, object], digest: str) -> dict[Path, str]:
    return {
        root / "desktop" / "RuntimeContract.generated.swift": render_swift(contract, digest),
        root / "web" / "runtime-contract.generated.js": render_javascript(contract, digest),
        root / "server" / "runtime_contract_generated.py": render_python(contract, digest),
        root / "scripts" / "runtime-contract.generated.sh": render_shell(contract, digest),
        root / "openclaw" / "openclaw.template.json5": render_openclaw_template(root, contract, digest),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    contract_path = root / "config" / "runtime-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    validate_contract(contract)
    digest = hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()
    stale: list[str] = []
    for path, expected in output_files(root, contract, digest).items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(str(path.relative_to(root)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if stale:
        raise SystemExit(
            "Runtime contract bindings are stale: " + ", ".join(stale)
            + ". Run scripts/generate-runtime-contract.py /path/to/jarvis-stark"
        )
    if args.check:
        print(f"Runtime contract verified: {digest}")


if __name__ == "__main__":
    main()
