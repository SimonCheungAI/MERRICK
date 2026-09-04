"""Project OpenClaw's model directory; catalog presence is not account access."""
from runtime_contract_generated import RUNTIME_CONTRACT

# Public catalog identities differ from the app's private execution routes.
CATALOG_PROVIDERS = {
    "codex": "openai", "openai": "openai", "anthropic": "anthropic",
    "claude-code": "anthropic", "gemini": "google", "kimi": "moonshot",
    "deepseek": "deepseek", "custom": "jarvis-compatible",
}


def provider_models(payload: object, provider: str) -> list[dict]:
    contract = RUNTIME_CONTRACT["providers"].get(provider)
    if not contract or not isinstance(payload, dict):
        return []
    rows = payload.get("models")
    if not isinstance(rows, list):
        return []
    identities = {CATALOG_PROVIDERS[provider], contract["runtimeRoute"]}
    if provider != "custom":
        identities.discard("jarvis-compatible")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("provider") not in identities:
            continue
        model = row.get("id")
        if not isinstance(model, str) or not model.strip() or len(model) > 120:
            continue
        result.setdefault(model, {"id": model, "name": str(row.get("name") or model), "source": "openclaw"})
    return sorted(result.values(), key=lambda model: model["id"])
