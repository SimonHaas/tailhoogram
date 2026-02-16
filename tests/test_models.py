"""Tests for data models."""

import pytest

from models import TailscaleEvent, WebhookRequest


@pytest.mark.unit
class TestWebhookRequest:
    """Tests for WebhookRequest convenience methods."""

    def test_webhook_request_iter(self, sample_tailscale_event) -> None:
        """Test iteration yields events."""
        events = [TailscaleEvent(**sample_tailscale_event)]
        request = WebhookRequest(root=events)

        assert list(request) == events

    def test_webhook_request_getitem(self, sample_tailscale_event) -> None:
        """Test indexing returns expected event."""
        events = [
            TailscaleEvent(**sample_tailscale_event),
            TailscaleEvent(**sample_tailscale_event),
        ]
        request = WebhookRequest(root=events)

        assert request[0].type == events[0].type
        assert request[1].tailnet == events[1].tailnet
