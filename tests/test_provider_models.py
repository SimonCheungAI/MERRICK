import sys
import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from provider_models import provider_models


class ProviderModelsTests(unittest.TestCase):
    def test_catalog_filters_provider_without_claiming_account_access(self):
        result = provider_models({"models": [
            {"provider": "openai", "id": "gpt-example", "name": "Example", "available": True},
            {"provider": "anthropic", "id": "claude-example"},
            {"provider": "openai", "id": "gpt-example"},
        ]}, "codex")
        self.assertEqual(result, [{"id": "gpt-example", "name": "Example", "source": "openclaw"}])

    def test_custom_catalog_never_mixes_other_providers(self):
        self.assertEqual(provider_models({"models": [
            {"provider": "openai", "id": "wrong"},
            {"provider": "jarvis-compatible", "id": "my-model"},
        ]}, "custom"), [{"id": "my-model", "name": "my-model", "source": "openclaw"}])

    def test_invalid_rows_and_unknown_provider_are_empty(self):
        self.assertEqual(provider_models({"models": [None, {}, {"provider": "openai", "id": ""}]}, "codex"), [])
        self.assertEqual(provider_models({"models": []}, "unknown"), [])


class ProviderCatalogSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalog_lookup_does_not_block_the_conversation_receiver(self):
        import main
        gate = asyncio.Event()
        requests = []
        async def gateway_request(*args, **kwargs):
            requests.append(args)
            await gate.wait()
            return {"models": [{"provider": "openai", "id": "demo"}]}
        session = main.Session.__new__(main.Session)
        session.provider_catalog_task = None
        session.send = AsyncMock()
        with patch.object(main.openclaw_gateway, "gateway_request", new=gateway_request):
            await session.handle_message({"type": "provider_models_request", "provider": "codex", "request_id": 7})
            self.assertFalse(session.provider_catalog_task.done())
            gate.set()
            await session.provider_catalog_task
        result = session.send.call_args.args[0]
        self.assertEqual(requests, [("models.list", {"view": "all"})])
        self.assertEqual(result["request_id"], 7)
        self.assertEqual(result["models"][0]["id"], "demo")

    async def test_catalog_failure_returns_a_retryable_empty_state(self):
        import main
        session = main.Session.__new__(main.Session)
        session.provider_catalog_task = None
        session.send = AsyncMock()
        with patch.object(main.openclaw_gateway, "gateway_request", new=AsyncMock(side_effect=RuntimeError("private diagnostic"))):
            await session.handle_message({"type": "provider_models_request", "provider": "codex", "request_id": 8})
            await session.provider_catalog_task
        self.assertEqual(session.send.call_args.args[0], {"type": "provider_models", "provider": "codex", "request_id": 8, "models": [], "status": "error"})
