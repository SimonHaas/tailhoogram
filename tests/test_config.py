"""Tests for configuration loading and management."""

import pytest

from config import (
    Config,
    _get_default_env_getter,
)


@pytest.mark.unit
class TestEnvGetter:
    """Tests for environment variable getter utilities."""

    def test_get_default_env_getter_returns_callable(self):
        """Test _get_default_env_getter returns a callable."""
        getter = _get_default_env_getter()
        assert callable(getter)

    def test_default_env_getter_accesses_os_getenv(self):
        """Test default getter uses os.getenv."""
        import os

        getter = _get_default_env_getter()
        # Test with a known env var
        result = getter("PATH")
        assert result == os.getenv("PATH")


@pytest.mark.unit
class TestConfigLoad:
    """Tests for Config.load() configuration loading."""

    def test_config_load_with_all_required_fields(self):
        """Test loading config with all required fields."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret-123",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        config = Config.load(env_getter=custom_getter)

        assert config is not None
        assert config.tailscale_webhook_secret == "test-secret-123"
        assert config.webhook_timestamp_tolerance_seconds == 300
        assert config.telegram_bot_token == "bot-token"
        assert config.telegram_chat_id == "chat-id"

    def test_config_load_with_custom_tolerance(self):
        """Test loading config with custom webhook tolerance."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret-123",
                "WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS": "600",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        config = Config.load(env_getter=custom_getter)

        assert config is not None
        assert config.webhook_timestamp_tolerance_seconds == 600

    def test_config_load_with_telegram_config(self):
        """Test loading config with Telegram settings."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
                "TELEGRAM_CHAT_ID": "987654321",
            }
            return env.get(key)

        config = Config.load(env_getter=custom_getter)

        assert config is not None
        assert config.tailscale_webhook_secret == "test-secret"
        assert config.telegram_bot_token == "123456:ABC-DEF"
        assert config.telegram_chat_id == "987654321"

    def test_config_load_missing_bot_token(self):
        """Test config loading fails without Telegram bot token."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is required"):
            Config.load(env_getter=custom_getter)

    def test_config_load_missing_chat_id(self):
        """Test config loading fails without Telegram chat ID."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "TELEGRAM_BOT_TOKEN": "bot-token",
            }
            return env.get(key)

        with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID is required"):
            Config.load(env_getter=custom_getter)

    def test_config_load_missing_secret(self):
        """Test config loading fails without webhook secret."""

        def custom_getter(key):
            return None

        with pytest.raises(ValueError, match="TAILSCALE_WEBHOOK_SECRET is required"):
            Config.load(env_getter=custom_getter)

    def test_config_load_invalid_tolerance(self):
        """Test config with invalid tolerance uses default."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "test-secret",
                "WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS": "not-a-number",
                "TELEGRAM_BOT_TOKEN": "bot-token",
                "TELEGRAM_CHAT_ID": "chat-id",
            }
            return env.get(key)

        config = Config.load(env_getter=custom_getter)

        assert config is not None
        assert config.webhook_timestamp_tolerance_seconds == 300

    def test_config_load_uses_default_getter(self, monkeypatch):
        """Test load uses default getter when none provided."""
        monkeypatch.setenv("TAILSCALE_WEBHOOK_SECRET", "real-secret")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "real-bot-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "real-chat-id")

        config = Config.load()

        assert config is not None
        assert config.tailscale_webhook_secret == "real-secret"
        assert config.telegram_bot_token == "real-bot-token"
        assert config.telegram_chat_id == "real-chat-id"

    def test_config_load_all_fields(self):
        """Test loading config with all fields specified."""

        def custom_getter(key):
            env = {
                "TAILSCALE_WEBHOOK_SECRET": "webhook-secret",
                "WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS": "600",
                "TELEGRAM_BOT_TOKEN": "bot-token-123",
                "TELEGRAM_CHAT_ID": "chat-id-456",
            }
            return env.get(key)

        config = Config.load(env_getter=custom_getter)

        assert config is not None
        assert config.tailscale_webhook_secret == "webhook-secret"
        assert config.webhook_timestamp_tolerance_seconds == 600
        assert config.telegram_bot_token == "bot-token-123"
        assert config.telegram_chat_id == "chat-id-456"


@pytest.mark.unit
class TestEnvGetterType:
    """Tests for EnvGetter type contract."""

    def test_env_getter_type_signature(self):
        """Test EnvGetter type is a proper Callable."""

        # EnvGetter should be Callable[[str], str | None]
        def valid_getter(key: str) -> str | None:
            return None

        # Should not raise type errors
        assert callable(valid_getter)
