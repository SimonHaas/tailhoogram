"""Pytest configuration and shared fixtures."""

import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from app import create_app

# Test environment constants
TEST_WEBHOOK_SECRET = "test-secret-key-12345"
TEST_TELEGRAM_BOT_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
TEST_TELEGRAM_CHAT_ID = "987654321"

# Set test environment variables before importing app
os.environ.setdefault("TAILSCALE_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)
os.environ.setdefault("TELEGRAM_BOT_TOKEN", TEST_TELEGRAM_BOT_TOKEN)
os.environ.setdefault("TELEGRAM_CHAT_ID", TEST_TELEGRAM_CHAT_ID)


@pytest.fixture
def app():
    """Create test FastAPI application."""
    # Use os.getenv for tests (reads from os.environ which is already set above)
    return create_app(env_getter=os.getenv)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def webhook_secret() -> str:
    """Test webhook secret."""
    return TEST_WEBHOOK_SECRET


@pytest.fixture
def webhook_secret_bytes(webhook_secret: str) -> bytes:
    """Test webhook secret as bytes."""
    return webhook_secret.encode("utf-8")


@pytest.fixture
def sample_tailscale_event() -> dict:
    """Sample Tailscale webhook event."""
    return {
        "timestamp": "2024-01-15T10:30:00Z",
        "version": 1,
        "type": "node.created",
        "tailnet": "example.com",
        "message": "Node created: my-laptop",
        "data": {
            "actor": "user@example.com",
            "nodeID": "12345",
            "nodeName": "my-laptop",
        },
    }


@pytest.fixture
def sample_webhook_body(sample_tailscale_event) -> bytes:
    """Sample webhook request body."""
    events = [sample_tailscale_event]
    body_str = json.dumps(events)
    return body_str.encode("utf-8")


def create_valid_signature(timestamp: int, body: bytes, secret: bytes) -> str:
    """
    Create valid HMAC-SHA256 signature for testing.

    Args:
        timestamp: Unix epoch timestamp
        body: Request body
        secret: Webhook secret

    Returns:
        Signature header value
    """
    signing_string = f"{timestamp}.{body.decode('utf-8')}".encode()
    signature = hmac.new(secret, signing_string, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture
def valid_signature(webhook_secret_bytes, sample_webhook_body) -> str:
    """Create valid signature for sample webhook body."""
    timestamp = int(time.time())
    return create_valid_signature(timestamp, sample_webhook_body, webhook_secret_bytes)


@pytest.fixture
def telegram_bot_token() -> str:
    """Test Telegram bot token."""
    return TEST_TELEGRAM_BOT_TOKEN


@pytest.fixture
def telegram_chat_id() -> str:
    """Test Telegram chat ID."""
    return TEST_TELEGRAM_CHAT_ID


@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Mock httpx.AsyncClient for testing."""

    class MockResponse:
        def __init__(self, status_code: int = 200, text: str = ""):
            self.status_code = status_code
            self.text = text

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            self.post_calls = []
            self.closed = False

        async def post(self, url, **kwargs):
            self.post_calls.append({"url": url, "kwargs": kwargs})
            return MockResponse(status_code=200)

        async def aclose(self):
            self.closed = True

    return MockAsyncClient()


@pytest.fixture
def monkeypatch_env(monkeypatch):
    """Fixture to easily set environment variables."""

    def set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))

    return set_env
