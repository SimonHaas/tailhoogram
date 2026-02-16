"""Tests for main entrypoint."""

import importlib
import sys
from types import SimpleNamespace


def _reload_main(monkeypatch, *, app_value=None, record_env=False):
    """Reload main module with patched dependencies."""
    import dotenv

    import app as app_module

    env_calls = {}

    if record_env:
        def fake_load(path):
            env_calls["path"] = path
            return True

        monkeypatch.setattr(dotenv, "load_dotenv", fake_load)

    if app_value is None:
        app_value = SimpleNamespace(name="app")

    monkeypatch.setattr(app_module, "create_app", lambda: app_value)

    if "main" in sys.modules:
        del sys.modules["main"]

    module = importlib.import_module("main")
    return module, env_calls


def test_main_loads_env_file(monkeypatch):
    """Test main loads .env file on import."""
    module, env_calls = _reload_main(monkeypatch, record_env=True)

    assert env_calls
    assert env_calls["path"].name == ".env"
    assert module.app is not None


def test_run_calls_uvicorn(monkeypatch):
    """Test run() calls uvicorn with expected args."""
    module, _env_calls = _reload_main(monkeypatch)

    calls = {}

    def fake_run(app, host, port):
        calls["app"] = app
        calls["host"] = host
        calls["port"] = port

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", fake_run)

    module.run()

    assert calls["app"] is module.app
    assert calls["host"] == "0.0.0.0"
    assert calls["port"] == 8000
