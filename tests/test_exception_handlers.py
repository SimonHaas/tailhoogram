"""Tests for exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exception_handlers import WebhookVerificationError, setup_exception_handlers


@pytest.fixture
def client() -> TestClient:
    """Create app with exception handlers."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/verification")
    def verification_error() -> None:
        raise WebhookVerificationError("invalid signature")

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    return TestClient(app, raise_server_exceptions=False)


def test_webhook_verification_handler(client: TestClient) -> None:
    """Test webhook verification errors return 401."""
    response = client.get("/verification")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature or timestamp"


def test_generic_exception_handler(client: TestClient) -> None:
    """Test generic errors return 500."""
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
