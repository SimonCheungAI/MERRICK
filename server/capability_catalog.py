"""Local, bounded inventory and enablement controls for OpenClaw capabilities.

Discovery remains compatible with the pinned OpenClaw CLI; reviewed mutations
use the official Gateway protocol. The HUD never edits JSON5, receives review
tokens, or accepts an install URL, package name, shell command, or arbitrary
config path. Users can change only an already-installed plugin or Skill after
OpenClaw returns its current capability review.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from harness_vault import safe_snapshot as harness_vault_snapshot
from openclaw_gateway_rpc import OpenClawGatewayRPCError
from runtime_contract_generated import DEFAULT_PROVIDER_ID, PROVIDERS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_DIR = (
    Path.home() / "Library" / "Application Support" / "JarvisStark" / "OpenClaw"
)
DEFAULT_WORKSPACE_DIR = (
    Path.home() / "Library" / "Application Support" / "JarvisStark" / "Workspace" / "Documents"
)
CAPABILITY_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")
PACKAGE_NAME_RE = re.compile(
    r"(?:@[A-Za-z0-9][A-Za-z0-9._-]{0,80}/)?[A-Za-z0-9][A-Za-z0-9._-]{0,120}\Z"
)
CATALOG_SCHEMA_VERSION = 1
MAX_SNAPSHOT_BYTES = 2_000_000

# These are part of MERRICK's own boot, model, memory and research path.
# Keeping them visible but immutable avoids a settings click turning the HUD
# into an unrecoverable offline app.
CORE_PLUGINS = frozenset({
    "jarvis-safe-tools", "codex", "openai", "anthropic", "google",
    "browser", "memory-core", "memory-wiki",
})

KNOWN_EXECUTION_PROFILES: dict[tuple[str, str], dict[str, Any]] = {
    ("plugin", "jarvis-safe-tools"): {
        "candidate_domains": ["desktop", "web", "media"],
        "effect_classes": ["read", "local_write"],
        "max_risk": "R1",
    },
    ("skill", "gog"): {
        "candidate_domains": ["mail", "calendar", "documents"],
        "effect_classes": ["read", "external_write"],
        "max_risk": "R2",
    },
    ("skill", "himalaya"): {
        "candidate_domains": ["mail"],
        "effect_classes": ["read", "external_write", "destructive"],
        "max_risk": "R3",
    },
}


class CapabilityCatalogError(RuntimeError):
    """A safe, concise management error for the local HUD."""


GatewayRequest = Callable[[str, Optional[dict[str, Any]]], Awaitable[object]]


def _runtime_paths() -> tuple[Path, Path]:
    node_dir = os.getenv("NODE_BIN_DIR", "").strip()
    candidates = [
        Path(node_dir) / "node" if node_dir else None,
        PROJECT_ROOT / "node" / "bin" / "node",
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node",
    ]
    node = next((path for path in candidates if path and path.is_file() and os.access(path, os.X_OK)), None)
    cli = PROJECT_ROOT / "node_modules" / "openclaw" / "openclaw.mjs"
    if node is None or not cli.is_file():
        raise CapabilityCatalogError("The bundled OpenClaw runtime is unavailable.")
    return node, cli


def _environment() -> dict[str, str]:
    state_dir = Path(os.getenv("OPENCLAW_STATE_DIR", DEFAULT_STATE_DIR))
    workspace = Path(os.getenv("JARVIS_WORKSPACE_DIR", DEFAULT_WORKSPACE_DIR))
    env = os.environ.copy()
    env.setdefault("JARVIS_PROJECT_ROOT", str(PROJECT_ROOT))
    env.setdefault("OPENCLAW_STATE_DIR", str(state_dir))
    env.setdefault("OPENCLAW_CONFIG_PATH", str(state_dir / "openclaw.json"))
    env.setdefault("JARVIS_WORKSPACE_DIR", str(workspace))
    default_provider = PROVIDERS[DEFAULT_PROVIDER_ID]
    env.setdefault("JARVIS_SELECTED_PROVIDER", DEFAULT_PROVIDER_ID)
    env.setdefault("JARVIS_SELECTED_MODEL", default_provider["defaultModel"])
    env.setdefault("JARVIS_SELECTED_BASE_URL", default_provider["defaultBaseUrl"])
    env.setdefault("JARVIS_MODEL_API_KEY", "unused")
    env.setdefault(
        "JARVIS_MAIN_MODEL",
        f"{default_provider['runtimeRoute']}/{default_provider['defaultModel']}",
    )
    env.setdefault("JARVIS_CONVERSATION_MODEL", env["JARVIS_MAIN_MODEL"])
    env.setdefault("JARVIS_OPENAI_RUNTIME", default_provider["openaiRuntime"])
    env.setdefault("JARVIS_ANTHROPIC_RUNTIME", default_provider["anthropicRuntime"])
    # OpenClaw 2026.8 resolves the gateway credential before `skills list`
    # starts. The app's gateway owner already keeps this token in a private
    # state file, so pass it only to this bounded child process and never to
    # WebKit, logs, or command-line arguments.
    token_path = Path(os.getenv("OPENCLAW_TOKEN_FILE", state_dir / ".gateway-token"))
    if "OPENCLAW_GATEWAY_TOKEN" not in env and token_path.is_file():
        try:
            token = token_path.read_text(encoding="utf-8").strip()
        except OSError:
            token = ""
        if re.fullmatch(r"[0-9a-fA-F]{64}", token):
            env["OPENCLAW_GATEWAY_TOKEN"] = token
    return env


async def _cli(
    *args: str,
    timeout: float = 35.0,
    allow_nonzero: bool = False,
) -> tuple[str, str]:
    node, cli = _runtime_paths()
    process = await asyncio.create_subprocess_exec(
        str(node), str(cli), *args,
        cwd=str(PROJECT_ROOT),
        env=_environment(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise CapabilityCatalogError("OpenClaw capability check timed out.")
    out, err = stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace")
    if process.returncode != 0 and not allow_nonzero:
        detail = (err or out).strip().splitlines()[-1:] or ["OpenClaw rejected the change."]
        raise CapabilityCatalogError(detail[0][:260])
    return out, err


def _json_output(value: str, label: str) -> dict[str, Any]:
    candidate = value.strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        object_start = candidate.find("{")
        if object_start < 0:
            raise CapabilityCatalogError(f"OpenClaw returned an invalid {label} inventory.") from exc
        try:
            parsed = json.loads(candidate[object_start:])
        except json.JSONDecodeError as nested_exc:
            raise CapabilityCatalogError(f"OpenClaw returned an invalid {label} inventory.") from nested_exc
    if not isinstance(parsed, dict):
        raise CapabilityCatalogError(f"OpenClaw returned an invalid {label} inventory.")
    return parsed


def _lifecycle_view(
    *,
    enabled: bool,
    ready: bool,
    requirements: list[str],
    review: str,
) -> dict[str, str]:
    """Return non-authoritative lifecycle facts for the capabilities HUD.

    Discovery, enablement, dependency readiness, connection and authorization
    are deliberately separate.  In particular, an enabled or eligible item is
    never presented as connected or authorized unless a later app-owned
    connector layer can prove those states.
    """
    if ready:
        readiness = "ready"
    elif requirements:
        readiness = "dependency_missing"
    elif not enabled:
        readiness = "disabled"
    else:
        readiness = "unhealthy"
    return {
        "discovery": "discovered",
        "enablement": "enabled" if enabled else "disabled",
        "readiness": readiness,
        "review": review,
        "connection": "not_assessed",
        "authorization": "policy_managed" if review == "core" else "not_assessed",
    }


def _execution_profile(kind: str, item_id: str) -> dict[str, Any]:
    """Return display-only conservative effect metadata.

    Even known candidates remain non-executable at this inventory boundary.
    A later reviewed connector binding must revalidate its schema, account,
    grant and exact risk before an operation can run.
    """
    known = KNOWN_EXECUTION_PROFILES.get((kind, item_id))
    if known is None:
        known = {
            "candidate_domains": [],
            "effect_classes": ["unknown"],
            "max_risk": "R3",
        }
    return {**known, "executable": False}


def _compatibility_hash(kind: str, item_id: str, contract: dict[str, Any]) -> str:
    encoded = json.dumps(
        {"kind": kind, "id": item_id, "contract": contract},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _snapshot_path() -> Path:
    state_dir = Path(os.getenv("OPENCLAW_STATE_DIR", DEFAULT_STATE_DIR))
    return state_dir / "cache" / "jarvis-capability-snapshot-v1.json"


def _adapter_enabled() -> bool:
    return os.getenv("JARVIS_CAPABILITY_ADAPTER_V1", "").strip().lower() == "true"


def _legacy_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    """Project the pre-adapter response for a one-switch rollback."""
    return {
        "plugins": [
            {key: value for key, value in item.items() if key not in {"lifecycle", "execution_profile", "compatibility_hash"}}
            for item in payload["plugins"]
        ],
        "skills": [
            {key: value for key, value in item.items() if key not in {"lifecycle", "execution_profile", "compatibility_hash"}}
            for item in payload["skills"]
        ],
        "summary": payload["summary"],
    }


def _save_snapshot(payload: dict[str, Any]) -> None:
    path = _snapshot_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            return
        temporary = path.with_suffix(".tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(path)
    except OSError:
        # The live inventory remains useful even when its optional fallback
        # cache cannot be written (read-only disk, permissions, full volume).
        return


def _load_snapshot() -> dict[str, Any] | None:
    path = _snapshot_path()
    try:
        if not path.is_file() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("plugins"), list)
        or not isinstance(payload.get("skills"), list)
        or not isinstance(payload.get("summary"), dict)
        or not isinstance(payload.get("snapshot"), dict)
        or payload["snapshot"].get("schema_version") != CATALOG_SCHEMA_VERSION
    ):
        return None
    payload["snapshot"]["stale"] = True
    payload["snapshot"]["last_error_code"] = "CAPABILITY_DISCOVERY_FAILED"
    return payload


def _plugin_view(plugin: dict[str, Any]) -> dict[str, Any] | None:
    plugin_id = plugin.get("id")
    if not isinstance(plugin_id, str) or not CAPABILITY_ID_RE.fullmatch(plugin_id):
        return None
    contracts = plugin.get("contracts") if isinstance(plugin.get("contracts"), dict) else {}
    surfaces = []
    declared_contract: dict[str, list[str]] = {}
    for key in ("tools", "commands", "channels", "providers", "skills", "webSearchProviders", "speechProviders"):
        values = contracts.get(key)
        if isinstance(values, list):
            normalized = [value[:160] for value in values[:64] if isinstance(value, str)]
            if normalized:
                declared_contract[key] = normalized
                surfaces.extend(normalized[:4])
    dependency = plugin.get("dependencyStatus") if isinstance(plugin.get("dependencyStatus"), dict) else {}
    enabled = bool(plugin.get("enabled"))
    status = str(plugin.get("status") or "unknown")[:40]
    dependencies_ok = bool(dependency.get("requiredInstalled", True))
    locked = plugin_id in CORE_PLUGINS
    requirements = [] if dependencies_ok else ["plugin_dependency"]
    return {
        "id": plugin_id,
        "name": str(plugin.get("name") or plugin_id)[:120],
        "description": str(plugin.get("description") or "No description supplied by OpenClaw.")[:420],
        "enabled": enabled,
        "status": status,
        "origin": str(plugin.get("origin") or "unknown")[:40],
        "version": str(plugin.get("version") or "")[:40],
        "locked": locked,
        "surfaces": list(dict.fromkeys(surfaces))[:8],
        "dependencies_ok": dependencies_ok,
        "lifecycle": _lifecycle_view(
            enabled=enabled,
            ready=status == "loaded" and dependencies_ok,
            requirements=requirements,
            review="core" if locked else "unreviewed",
        ),
        "execution_profile": _execution_profile("plugin", plugin_id),
        "compatibility_hash": _compatibility_hash("plugin", plugin_id, declared_contract),
    }


def _skill_view(skill: dict[str, Any]) -> dict[str, Any] | None:
    name = skill.get("name")
    if not isinstance(name, str) or not CAPABILITY_ID_RE.fullmatch(name):
        return None
    missing = skill.get("missing") if isinstance(skill.get("missing"), dict) else {}
    requirements = []
    for key in ("bins", "env", "config", "os"):
        values = missing.get(key)
        if isinstance(values, list):
            requirements.extend(str(value) for value in values[:4] if isinstance(value, str))
    enabled = not bool(skill.get("disabled"))
    eligible = bool(skill.get("eligible"))
    requirements = list(dict.fromkeys(requirements))[:8]
    return {
        "id": name,
        "name": name,
        "description": str(skill.get("description") or "No description supplied by OpenClaw.")[:420],
        "emoji": str(skill.get("emoji") or "◈")[:8],
        "enabled": enabled,
        "eligible": eligible,
        "visible": bool(skill.get("modelVisible")),
        "source": str(skill.get("source") or "unknown")[:60],
        "bundled": bool(skill.get("bundled")),
        "requirements": requirements,
        "homepage": str(skill.get("homepage") or "")[:500],
        "lifecycle": _lifecycle_view(
            enabled=enabled,
            ready=eligible,
            requirements=requirements,
            review="unreviewed",
        ),
        "execution_profile": _execution_profile("skill", name),
        "compatibility_hash": _compatibility_hash(
            "skill",
            name,
            {
                "source": str(skill.get("source") or "unknown")[:160],
                "requirements": requirements,
                "bundled": bool(skill.get("bundled")),
            },
        ),
    }


async def inventory() -> dict[str, Any]:
    adapter_enabled = _adapter_enabled()
    try:
        (plugin_output, _), (skill_output, _) = await asyncio.gather(
            _cli("plugins", "list", "--json", timeout=45.0),
            _cli("skills", "list", "--json", "--agent", "main", timeout=45.0),
        )
    except CapabilityCatalogError:
        cached = _load_snapshot() if adapter_enabled else None
        if cached is not None:
            cached["harness"] = harness_vault_snapshot()
            return cached
        raise
    plugins_raw = _json_output(plugin_output, "plugin").get("plugins", [])
    skills_raw = _json_output(skill_output, "skill").get("skills", [])
    plugins = [item for raw in plugins_raw if isinstance(raw, dict) if (item := _plugin_view(raw))]
    skills = [item for raw in skills_raw if isinstance(raw, dict) if (item := _skill_view(raw))]
    plugins.sort(key=lambda item: (not item["enabled"], item["locked"], item["name"].casefold()))
    skills.sort(key=lambda item: (not item["eligible"], not item["enabled"], item["name"].casefold()))
    payload = {
        "plugins": plugins,
        "skills": skills,
        "summary": {
            "plugins_total": len(plugins),
            "plugins_enabled": sum(item["enabled"] for item in plugins),
            "skills_total": len(skills),
            "skills_ready": sum(item["eligible"] and item["enabled"] for item in skills),
        },
        "snapshot": {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stale": False,
        },
    }
    if not adapter_enabled:
        return _legacy_inventory(payload)
    payload["harness"] = harness_vault_snapshot()
    _save_snapshot(payload)
    return payload


async def set_plugin_enabled(plugin_id: str, enabled: bool) -> None:
    if not CAPABILITY_ID_RE.fullmatch(plugin_id):
        raise CapabilityCatalogError("Invalid plugin identifier.")
    if plugin_id in CORE_PLUGINS:
        raise CapabilityCatalogError("This is a MERRICK core plugin and cannot be disabled here.")
    await _cli("plugins", "enable" if enabled else "disable", plugin_id, timeout=35.0)


async def set_skill_enabled(skill_id: str, enabled: bool) -> None:
    if not CAPABILITY_ID_RE.fullmatch(skill_id):
        raise CapabilityCatalogError("Invalid skill identifier.")
    # `config set` performs one schema-validated JSON5 mutation rather than
    # letting the WebView write a file.  It is intentionally limited to the
    # exact enabled boolean of an already-discovered local skill.
    await _cli(
        "config", "set", f"skills.entries.{skill_id}.enabled",
        "true" if enabled else "false", "--strict-json", timeout=35.0,
    )


def _review_surfaces(declared: dict[str, Any]) -> list[dict[str, Any]]:
    labels = {
        "channels": "Channels", "providers": "Model providers", "tools": "Tools",
        "hooks": "Hooks", "mcpServers": "MCP servers", "cliCommands": "CLI commands",
        "skills": "Skills", "dangerousConfigFlags": "Sensitive configuration",
    }
    surfaces = []
    for key, label in labels.items():
        values = declared.get(key)
        if not isinstance(values, list):
            continue
        clean = [str(value)[:120] for value in values if isinstance(value, str)][:12]
        if clean:
            surfaces.append({"key": key, "label": label, "count": len(values), "items": clean})
    return surfaces


async def prepare_gateway_change(
    kind: str,
    capability_id: str,
    enabled: bool,
    gateway_request: GatewayRequest,
) -> dict[str, Any]:
    """Build a server-held change and a redacted review for the HUD.

    Review tokens never cross into WebKit. The caller stores the returned
    object server-side and sends only its ``public`` member to the browser.
    """
    if kind not in {"plugin", "skill"} or not CAPABILITY_ID_RE.fullmatch(capability_id):
        raise CapabilityCatalogError("Invalid capability change request.")
    if kind == "plugin":
        if capability_id in CORE_PLUGINS and not enabled:
            raise CapabilityCatalogError("This MERRICK core plugin cannot be disabled.")
        raw = await gateway_request("plugins.inspect", {"pluginId": capability_id})
        if not isinstance(raw, dict) or raw.get("ok") is not True:
            raise CapabilityCatalogError("OpenClaw could not inspect that plugin.")
        plugin = raw.get("plugin") if isinstance(raw.get("plugin"), dict) else {}
        if plugin.get("id") != capability_id or plugin.get("installed") is not True:
            raise CapabilityCatalogError("That plugin is not installed in this OpenClaw workspace.")
        trust = raw.get("trust") if isinstance(raw.get("trust"), dict) else {}
        disposition = str(trust.get("disposition") or "bundled")[:40]
        if enabled and disposition == "blocked":
            raise CapabilityCatalogError("OpenClaw blocked this plugin after its security review.")
        review_token = raw.get("reviewToken")
        if not isinstance(review_token, str) or not review_token:
            raise CapabilityCatalogError("OpenClaw did not return a valid capability review.")
        declared = raw.get("declared") if isinstance(raw.get("declared"), dict) else {}
        public = {
            "kind": kind,
            "id": capability_id,
            "enabled": enabled,
            "name": str(plugin.get("name") or capability_id)[:120],
            "description": str(plugin.get("description") or "")[:420],
            "trust": disposition,
            "surfaces": _review_surfaces(declared),
        }
        return {"public": public, "review_token": review_token}

    raw = await gateway_request("skills.status", {"agentId": "main"})
    skills = raw.get("skills") if isinstance(raw, dict) else None
    skill = next(
        (item for item in skills or [] if isinstance(item, dict) and item.get("skillKey") == capability_id),
        None,
    )
    if skill is None:
        raise CapabilityCatalogError("That Skill is not installed for the main OpenClaw agent.")
    missing = skill.get("missing") if isinstance(skill.get("missing"), dict) else {}
    requirements = []
    for values in missing.values():
        if isinstance(values, list):
            requirements.extend(str(value)[:120] for value in values if isinstance(value, str))
    public = {
        "kind": kind,
        "id": capability_id,
        "enabled": enabled,
        "name": str(skill.get("name") or capability_id)[:120],
        "description": str(skill.get("description") or "")[:420],
        "trust": "installed-skill",
        "surfaces": [],
        "requirements": list(dict.fromkeys(requirements))[:12],
    }
    return {"public": public}


async def apply_gateway_change(
    prepared: dict[str, Any],
    gateway_request: GatewayRequest,
) -> bool:
    """Apply one previously reviewed change through OpenClaw's official RPC."""
    public = prepared.get("public") if isinstance(prepared.get("public"), dict) else {}
    kind, capability_id, enabled = public.get("kind"), public.get("id"), public.get("enabled")
    if kind not in {"plugin", "skill"} or not isinstance(capability_id, str) or not isinstance(enabled, bool):
        raise CapabilityCatalogError("The capability review expired or was invalid.")
    if kind == "plugin":
        params: dict[str, Any] = {"pluginId": capability_id, "enabled": enabled}
        review_token = prepared.get("review_token")
        if enabled and isinstance(review_token, str) and review_token:
            params["acknowledgeCapabilities"] = {"reviewToken": review_token}
        raw = await gateway_request("plugins.setEnabled", params)
        if not isinstance(raw, dict) or raw.get("ok") is not True:
            raise CapabilityCatalogError("OpenClaw did not apply that plugin change.")
        return bool(raw.get("restartRequired"))
    raw = await gateway_request("skills.update", {"skillKey": capability_id, "enabled": enabled})
    if not isinstance(raw, dict):
        raise CapabilityCatalogError("OpenClaw did not apply that Skill change.")
    return False


async def diagnostics() -> list[dict[str, str]]:
    # `doctor --lint` returns non-zero when warnings are found; those warnings
    # are the useful result for this read-only UI rather than an operation
    # failure, so parse its JSON envelope either way.
    output, _ = await _cli(
        "doctor", "--lint", "--json", "--non-interactive",
        timeout=50.0, allow_nonzero=True,
    )
    payload = _json_output(output, "diagnostic")
    findings = payload.get("findings", payload.get("issues", []))
    if not isinstance(findings, list):
        findings = []
    result = []
    for finding in findings[:40]:
        if not isinstance(finding, dict):
            continue
        result.append({
            "severity": str(finding.get("severity") or finding.get("level") or "info")[:20],
            "message": str(finding.get("message") or finding.get("title") or "OpenClaw diagnostic")[:420],
        })
    return result


def _catalog_install_identity(entry: dict[str, Any]) -> tuple[str, str] | None:
    install = entry.get("install") if isinstance(entry.get("install"), dict) else {}
    source = install.get("source")
    if source == "official":
        identity = install.get("pluginId")
        if isinstance(identity, str) and CAPABILITY_ID_RE.fullmatch(identity):
            return source, identity
    if source == "clawhub":
        identity = install.get("packageName")
        if isinstance(identity, str) and PACKAGE_NAME_RE.fullmatch(identity):
            return source, identity
    return None


def _catalog_entry_view(entry: dict[str, Any]) -> dict[str, Any] | None:
    plugin_id = entry.get("id")
    if not isinstance(plugin_id, str) or not plugin_id or len(plugin_id) > 160:
        return None
    identity = _catalog_install_identity(entry)
    origin = str(entry.get("origin") or "")[:40]
    return {
        "key": f"plugin:{plugin_id}",
        "plugin_id": plugin_id,
        "name": str(entry.get("name") or plugin_id)[:120],
        "description": str(entry.get("description") or "")[:420],
        "version": str(entry.get("version") or "")[:40],
        "category": str(entry.get("category") or "other")[:40],
        "featured": bool(entry.get("featured")),
        "installed": bool(entry.get("installed")),
        "enabled": bool(entry.get("enabled")),
        "removable": bool(entry.get("removable")),
        "origin": origin,
        "install_source": identity[0] if identity else "",
        "install_identity": identity[1] if identity else "",
        "official": bool(identity and identity[0] == "official") or origin in {"bundled", "official"},
    }


def _search_entry_view(entry: dict[str, Any]) -> dict[str, Any] | None:
    package = entry.get("package") if isinstance(entry.get("package"), dict) else {}
    name = package.get("name")
    if not isinstance(name, str) or not PACKAGE_NAME_RE.fullmatch(name):
        return None
    channel = str(package.get("channel") or "community")[:24]
    return {
        "key": f"clawhub:{name}",
        "plugin_id": str(package.get("runtimeId") or "")[:160],
        "name": str(package.get("displayName") or name)[:120],
        "description": str(package.get("summary") or name)[:420],
        "version": str(package.get("latestVersion") or "")[:40],
        "category": "clawhub",
        "featured": False,
        "installed": False,
        "enabled": False,
        "removable": False,
        "install_source": "clawhub",
        "install_identity": name,
        "official": bool(package.get("isOfficial")),
        "channel": channel,
        "downloads": int(package.get("downloads") or 0),
        "verification": str(package.get("verificationTier") or "")[:60],
    }


async def discover_plugins(
    gateway_request: GatewayRequest,
    query: str = "",
) -> dict[str, Any]:
    """Return OpenClaw's own curated catalog plus bounded ClawHub search."""
    clean_query = query.strip()[:120]
    raw = await gateway_request("plugins.list", {})
    if not isinstance(raw, dict) or not isinstance(raw.get("plugins"), list):
        raise CapabilityCatalogError("OpenClaw returned an invalid plugin catalog.")
    catalog = [
        view for item in raw["plugins"] if isinstance(item, dict)
        if (view := _catalog_entry_view(item)) is not None
    ]
    if clean_query:
        folded = clean_query.casefold()
        catalog = [
            item for item in catalog
            if folded in " ".join((item["name"], item["description"], item["plugin_id"], item["install_identity"])).casefold()
        ]
    else:
        # The Installed tab already owns the complete local inventory. Keep the
        # landing catalog intentionally small so bundled providers do not bury
        # the plugins OpenClaw actually recommends discovering.
        catalog = [item for item in catalog if item["featured"] or item["removable"]]

    search_results: list[dict[str, Any]] = []
    if len(clean_query) >= 2:
        searched = await gateway_request("plugins.search", {"query": clean_query, "limit": 24})
        results = searched.get("results") if isinstance(searched, dict) else None
        if not isinstance(results, list):
            raise CapabilityCatalogError("OpenClaw returned an invalid ClawHub search result.")
        search_results = [
            view for item in results if isinstance(item, dict)
            if (view := _search_entry_view(item)) is not None
        ]

    installed_packages = {
        item["install_identity"] for item in catalog
        if item["installed"] and item["install_identity"]
    }
    for item in search_results:
        if item["install_identity"] in installed_packages:
            item["installed"] = True
    merged: dict[str, dict[str, Any]] = {item["key"]: item for item in catalog}
    for item in search_results:
        merged.setdefault(item["key"], item)
    entries = sorted(
        merged.values(),
        key=lambda item: (not item["featured"], item["installed"], not item["official"], item["name"].casefold()),
    )[:80]
    return {
        "catalog": entries,
        "query": clean_query,
        "mutation_allowed": bool(raw.get("mutationAllowed")),
    }


def _review_grants(grants: dict[str, Any]) -> list[dict[str, Any]]:
    hooks = grants.get("hooks") if isinstance(grants.get("hooks"), dict) else {}
    result = []
    for key, label in (
        ("allowPromptInjection", "Prompt injection"),
        ("allowConversationAccess", "Conversation access"),
    ):
        grant = hooks.get(key) if isinstance(hooks.get(key), dict) else {}
        result.append({"key": key, "label": label, "effective": bool(grant.get("effective"))})
    return result


def _safe_source(source: dict[str, Any]) -> dict[str, str]:
    kind = str(source.get("kind") or "unknown")[:40]
    return {
        "kind": kind,
        "spec": str(source.get("spec") or "")[:240],
        "package_name": str(source.get("packageName") or "")[:160],
        "integrity": str(source.get("integrity") or "")[:300],
        "integrity_kind": str(source.get("integrityKind") or "")[:40],
    }


async def _resolve_install_candidate(
    source: str,
    identity: str,
    gateway_request: GatewayRequest,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if source == "official" and not CAPABILITY_ID_RE.fullmatch(identity):
        raise CapabilityCatalogError("Invalid official plugin identifier.")
    if source == "clawhub" and not PACKAGE_NAME_RE.fullmatch(identity):
        raise CapabilityCatalogError("Invalid ClawHub package name.")
    listing = await gateway_request("plugins.list", {})
    plugins = listing.get("plugins") if isinstance(listing, dict) else None
    if not isinstance(plugins, list) or listing.get("mutationAllowed") is not True:
        raise CapabilityCatalogError("OpenClaw plugin changes are unavailable right now.")
    for item in plugins:
        if not isinstance(item, dict):
            continue
        install_identity = _catalog_install_identity(item)
        if install_identity == (source, identity):
            return item, {"source": source, "pluginId" if source == "official" else "packageName": identity}
    if source == "clawhub":
        searched = await gateway_request("plugins.search", {"query": identity, "limit": 20})
        results = searched.get("results") if isinstance(searched, dict) else None
        match = next(
            (
                item.get("package") for item in results or []
                if isinstance(item, dict)
                and isinstance(item.get("package"), dict)
                and item["package"].get("name") == identity
            ),
            None,
        )
        if isinstance(match, dict):
            request: dict[str, Any] = {"source": "clawhub", "packageName": identity}
            if isinstance(match.get("latestVersion"), str):
                request["version"] = match["latestVersion"][:40]
            return {
                "id": str(match.get("runtimeId") or identity),
                "name": str(match.get("displayName") or identity),
                "description": str(match.get("summary") or ""),
                "version": str(match.get("latestVersion") or ""),
                "installed": False,
                "enabled": False,
                "removable": False,
                "channel": str(match.get("channel") or "community"),
                "verification": str(match.get("verificationTier") or ""),
                "downloads": int(match.get("downloads") or 0),
            }, request
    raise CapabilityCatalogError("That plugin is no longer available from OpenClaw's catalog.")


async def prepare_plugin_operation(
    action: str,
    identity: str,
    source: str,
    gateway_request: GatewayRequest,
) -> dict[str, Any]:
    """Prepare a server-held install, update, or uninstall confirmation."""
    if action not in {"install", "upgrade", "uninstall"}:
        raise CapabilityCatalogError("Invalid plugin operation.")
    if action in {"install", "upgrade"}:
        entry, request = await _resolve_install_candidate(source, identity, gateway_request)
        if action == "install" and entry.get("installed") is True:
            raise CapabilityCatalogError("That plugin is already installed.")
        public = {
            "kind": "plugin",
            "action": action,
            "stage": "identity",
            "id": str(entry.get("id") or identity)[:160],
            "name": str(entry.get("name") or identity)[:120],
            "description": str(entry.get("description") or "")[:420],
            "source": source,
            "identity": identity,
            "version": str(request.get("version") or entry.get("version") or "")[:40],
            "channel": str(entry.get("channel") or ("official" if source == "official" else "clawhub"))[:40],
            "verification": str(entry.get("verification") or "")[:60],
            "downloads": int(entry.get("downloads") or 0),
            "surfaces": [],
            "grants": [],
        }
        return {"public": public, "request": request}

    if not CAPABILITY_ID_RE.fullmatch(identity) or identity in CORE_PLUGINS:
        raise CapabilityCatalogError("That plugin cannot be removed from MERRICK")
    listing = await gateway_request("plugins.list", {})
    plugins = listing.get("plugins") if isinstance(listing, dict) else None
    entry = next(
        (item for item in plugins or [] if isinstance(item, dict) and item.get("id") == identity),
        None,
    )
    if not isinstance(entry, dict) or entry.get("installed") is not True or entry.get("removable") is not True:
        raise CapabilityCatalogError("That plugin is not removable in this OpenClaw workspace.")
    inspected = await gateway_request("plugins.inspect", {"pluginId": identity})
    declared = inspected.get("declared") if isinstance(inspected, dict) and isinstance(inspected.get("declared"), dict) else {}
    grants = inspected.get("grants") if isinstance(inspected, dict) and isinstance(inspected.get("grants"), dict) else {}
    source_info = inspected.get("source") if isinstance(inspected, dict) and isinstance(inspected.get("source"), dict) else {}
    public = {
        "kind": "plugin",
        "action": action,
        "stage": "removal",
        "id": identity,
        "name": str(entry.get("name") or identity)[:120],
        "description": str(entry.get("description") or "")[:420],
        "source_info": _safe_source(source_info),
        "surfaces": _review_surfaces(declared),
        "grants": _review_grants(grants),
    }
    return {"public": public, "request": {"pluginId": identity}}


def _capability_consent(details: Any) -> dict[str, Any] | None:
    if not isinstance(details, dict) or details.get("capabilityConsentCode") != "PLUGIN_CAPABILITY_CONSENT_REQUIRED":
        return None
    plugin_id, token = details.get("pluginId"), details.get("reviewToken")
    if not isinstance(plugin_id, str) or not CAPABILITY_ID_RE.fullmatch(plugin_id):
        return None
    if not isinstance(token, str) or not token or len(token) > 512:
        return None
    widened = details.get("widened") if isinstance(details.get("widened"), dict) else {}
    return {"plugin_id": plugin_id, "review_token": token, "widened": widened}


def _install_policy_warning(details: Any) -> dict[str, Any] | None:
    if not isinstance(details, dict) or details.get("installPolicyCode") != "install_policy_warning_acknowledgement_required":
        return None
    findings = []
    for finding in details.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        findings.append({
            "severity": str(finding.get("severity") or "warn")[:20],
            "message": str(finding.get("message") or "")[:420],
            "file": str(finding.get("file") or "")[:240],
            "line": int(finding.get("line") or 0),
        })
    return {
        "reason": str(details.get("reason") or "OpenClaw recommends reviewing this package.")[:600],
        "findings": findings[:30],
    }


async def apply_plugin_operation(
    prepared: dict[str, Any],
    gateway_request: GatewayRequest,
) -> dict[str, Any]:
    """Apply one confirmed plugin operation or return its next review stage."""
    public = prepared.get("public") if isinstance(prepared.get("public"), dict) else {}
    request = prepared.get("request") if isinstance(prepared.get("request"), dict) else {}
    action = public.get("action")
    if action == "uninstall":
        result = await gateway_request("plugins.uninstall", request)
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise CapabilityCatalogError("OpenClaw did not uninstall that plugin.")
        return {"status": "changed", "restart_required": bool(result.get("restartRequired")), "result": result}
    if action not in {"install", "upgrade"}:
        raise CapabilityCatalogError("The plugin operation expired or was invalid.")

    install_request = dict(request)
    if prepared.get("acknowledge_policy") is True:
        install_request["acknowledgeInstallPolicyWarning"] = True
    review_token = prepared.get("review_token")
    if isinstance(review_token, str) and review_token:
        install_request["acknowledgeCapabilities"] = {"reviewToken": review_token}
    try:
        result = await gateway_request("plugins.install", install_request)
    except OpenClawGatewayRPCError as exc:
        consent = _capability_consent(exc.details)
        if consent is not None:
            inspected = await gateway_request("plugins.inspect", {"pluginId": consent["plugin_id"]})
            declared = inspected.get("declared") if isinstance(inspected, dict) and isinstance(inspected.get("declared"), dict) else consent["widened"]
            grants = inspected.get("grants") if isinstance(inspected, dict) and isinstance(inspected.get("grants"), dict) else {}
            source_info = inspected.get("source") if isinstance(inspected, dict) and isinstance(inspected.get("source"), dict) else {}
            plugin = inspected.get("plugin") if isinstance(inspected, dict) and isinstance(inspected.get("plugin"), dict) else {}
            trust = inspected.get("trust") if isinstance(inspected, dict) and isinstance(inspected.get("trust"), dict) else {}
            prepared["review_token"] = consent["review_token"]
            prepared["public"] = {
                **public,
                "stage": "capabilities",
                "id": consent["plugin_id"],
                "name": str(plugin.get("name") or public.get("name") or consent["plugin_id"])[:120],
                "description": str(plugin.get("description") or public.get("description") or "")[:420],
                "trust": str(trust.get("disposition") or public.get("channel") or "unreviewed")[:40],
                "source_info": _safe_source(source_info),
                "surfaces": _review_surfaces(declared),
                "grants": _review_grants(grants),
            }
            return {"status": "review", "prepared": prepared}
        warning = _install_policy_warning(exc.details)
        if warning is not None:
            prepared["acknowledge_policy"] = True
            prepared["public"] = {**public, "stage": "policy", **warning}
            return {"status": "review", "prepared": prepared}
        raise CapabilityCatalogError(str(exc)[:300]) from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise CapabilityCatalogError("OpenClaw did not install that plugin.")
    return {"status": "changed", "restart_required": bool(result.get("restartRequired")), "result": result}
