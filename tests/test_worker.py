"""Tests for Cloudflare worker entrypoint."""

from types import ModuleType, SimpleNamespace
import importlib
import sys

import pytest


def _load_worker_module(monkeypatch):
    """Import worker with a stubbed workers module."""
    fake_workers = ModuleType("workers")

    class FakeWorkerEntrypoint:
        def __init__(self, *args, **kwargs):
            self.env = None

    fake_workers.WorkerEntrypoint = FakeWorkerEntrypoint  # type: ignore
    monkeypatch.setitem(sys.modules, "workers", fake_workers)

    if "worker" in sys.modules:
        del sys.modules["worker"]

    return importlib.import_module("worker")


@pytest.mark.unit
def test_worker_get_app_caches(monkeypatch):
    """Test _get_app caches instance and uses env getter."""
    worker_module = _load_worker_module(monkeypatch)
    created = []

    def fake_create_app(env_getter):
        created.append(env_getter)
        return "APP"

    monkeypatch.setattr(worker_module, "create_app", fake_create_app)

    instance = worker_module.Default()
    instance.env = SimpleNamespace(TEST_KEY="value")

    app_first = instance._get_app()
    app_second = instance._get_app()

    assert app_first == "APP"
    assert app_second == "APP"
    assert len(created) == 1
    assert created[0]("TEST_KEY") == "value"


@pytest.mark.asyncio
async def test_worker_fetch_uses_asgi(monkeypatch):
    """Test fetch delegates to asgi.fetch."""
    worker_module = _load_worker_module(monkeypatch)
    instance = worker_module.Default()
    instance.env = SimpleNamespace()
    instance._app = "APP"

    request = SimpleNamespace(js_object="REQUEST")

    async def fake_fetch(app, request_obj, env):
        return {"app": app, "request": request_obj, "env": env}

    fake_asgi = ModuleType("asgi")
    fake_asgi.fetch = fake_fetch  # type: ignore
    monkeypatch.setitem(sys.modules, "asgi", fake_asgi)

    response = await instance.fetch(request)

    assert response["app"] == "APP"
    assert response["request"] == "REQUEST"
    assert response["env"] is instance.env
