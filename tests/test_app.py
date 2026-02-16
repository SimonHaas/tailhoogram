"""Tests for API application factory and initialization."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app import create_app, process_webhook_events
from config import _get_default_env_getter
from models import TailscaleEvent


@pytest.mark.unit
class TestCreateApp:
    """Tests for FastAPI app factory."""

    def test_create_app_with_custom_getter(self):
        """Test create_app with custom env getter."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        assert app is not None
        assert app.state.config is not None
        assert app.state.telegram_channel is not None

    def test_create_app_config_stored(self):
        """Test create_app stores config in app state."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        assert app.state.config.tailscale_webhook_secret == "test-secret"
        assert app.state.config.telegram_bot_token == "bot-token"
        assert app.state.config.telegram_chat_id == "chat-id"

    def test_create_app_telegram_channel_stored(self):
        """Test create_app stores Telegram channel in app state."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        assert app.state.telegram_channel is not None
        from telegram import TelegramNotificationChannel

        assert isinstance(app.state.telegram_channel, TelegramNotificationChannel)

    def test_create_app_has_lifespan(self):
        """Test create_app sets up lifespan."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        # FastAPI app should have lifespan configured
        assert app.router.lifespan is not None

    def test_create_app_missing_secret_raises(self):
        """Test create_app raises on missing secret."""

        def custom_getter(key):
            env = {
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        with pytest.raises(ValueError, match="TAILSCALE_WEBHOOK_SECRET is required"):
            create_app(env_getter=custom_getter)

    def test_create_app_missing_telegram_token_raises(self):
        """Test create_app raises on missing Telegram bot token."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is required"):
            create_app(env_getter=custom_getter)

    def test_create_app_missing_telegram_chat_id_raises(self):
        """Test create_app raises on missing Telegram chat ID."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
            }
            return env.get(key)

        with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID is required"):
            create_app(env_getter=custom_getter)

    def test_create_app_telegram_init_failure_raises(self, monkeypatch):
        """Test create_app raises when Telegram channel init fails."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        class BadChannel:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("boom")

        import telegram as telegram_module

        monkeypatch.setattr(telegram_module, "TelegramNotificationChannel", BadChannel)

        with pytest.raises(RuntimeError, match="boom"):
            create_app(env_getter=custom_getter)

    def test_create_app_uses_default_getter(self, monkeypatch):
        """Test create_app uses default getter when none provided."""
        monkeypatch.setenv("TAILSCALE_WEBHOOK_SECRET", "real-secret")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "real-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "real-chat-id")

        app = create_app()

        assert app.state.config.tailscale_webhook_secret == "real-secret"
        assert app.state.config.telegram_bot_token == "real-token"
        assert app.state.config.telegram_chat_id == "real-chat-id"

    def test_create_app_with_telegram_config(self):
        """Test create_app includes Telegram channel."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        assert app.state.telegram_channel is not None
        assert app.state.telegram_channel.bot_token == "bot-token"

    def test_create_app_without_telegram_config(self):
        """Test create_app raises without Telegram config."""

        def custom_getter(key):
            env = {"TAILSCALE_WEBHOOK_SECRET": "test-secret"}
            return env.get(key)

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is required"):
            create_app(env_getter=custom_getter)

    def test_create_app_includes_webhook_endpoint(self):
        """Test create_app includes webhook endpoint."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        # Check for webhook endpoint
        routes = [getattr(route, "path", None) for route in app.routes]
        assert any("/events" in str(route) for route in routes if route)

    def test_create_app_has_exception_handlers(self):
        """Test create_app sets up exception handlers."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        app = create_app(env_getter=custom_getter)

        # Should have exception handlers configured
        assert app.exception_handlers is not None


@pytest.mark.unit
class TestEnvGetterDefault:
    """Tests for default environment getter in app."""

    def test_default_getter_is_correct(self):
        """Test default getter is os.getenv."""
        getter = _get_default_env_getter()

        import os

        test_var = "TEST_UNIQUE_VAR_12345"
        os.environ[test_var] = "test_value"

        result = getter(test_var)

        assert result == "test_value"

        del os.environ[test_var]


@pytest.mark.unit
class TestLifespan:
    """Tests for app lifespan cleanup."""

    @pytest.mark.asyncio
    async def test_lifespan_closes_channel(self, app):
        """Test lifespan shutdown closes the Telegram channel."""
        close_mock = AsyncMock()
        app.state.telegram_channel = MagicMock(close=close_mock)

        async with app.router.lifespan_context(app):
            pass

        close_mock.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lifespan_no_channel(self, app):
        """Test lifespan shutdown skips when channel is missing."""
        app.state.telegram_channel = None

        async with app.router.lifespan_context(app):
            pass


@pytest.mark.unit
class TestProcessWebhookEvents:
    """Tests for webhook event processing."""

    @pytest.mark.asyncio
    async def test_process_events_without_channel(self, sample_tailscale_event):
        """Test processing skips notifications when channel is missing."""
        events = [TailscaleEvent(**sample_tailscale_event)]

        result = await process_webhook_events(events, None)

        assert result is True

    @pytest.mark.asyncio
    async def test_process_events_partial_failure(self, sample_tailscale_event):
        """Test processing returns False when any send fails."""
        events = [
            TailscaleEvent(**sample_tailscale_event),
            TailscaleEvent(**sample_tailscale_event),
        ]
        channel = MagicMock()
        channel.send = AsyncMock(side_effect=[True, False])

        result = await process_webhook_events(events, channel)

        assert result is False
        assert channel.send.call_count == 2

    @pytest.mark.asyncio
    async def test_process_events_exception(self, sample_tailscale_event):
        """Test processing returns False when send raises."""
        events = [TailscaleEvent(**sample_tailscale_event)]
        channel = MagicMock()
        channel.send = AsyncMock(side_effect=RuntimeError("boom"))

        result = await process_webhook_events(events, channel)

        assert result is False
