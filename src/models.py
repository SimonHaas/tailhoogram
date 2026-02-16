"""Data models for Tailscale webhooks."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class TailscaleEventData(BaseModel):
    """Data payload of a Tailscale event."""

    model_config = ConfigDict(extra="allow")


class TailscaleEvent(BaseModel):
    """A single Tailscale webhook event."""

    model_config = ConfigDict(extra="allow")

    timestamp: datetime
    version: int
    type: str  # e.g., "node.created", "node.deleted", "node.key-expired"
    tailnet: str  # The domain name
    message: str  # Human-readable description
    data: dict[str, Any] = Field(default_factory=dict)  # Event-specific data


class WebhookRequest(RootModel):
    """Tailscale webhook request body (array of events)."""

    root: list[TailscaleEvent]

    def __iter__(self):
        """Allow iteration over events."""
        return iter(self.root)

    def __getitem__(self, index: int):
        """Allow indexing into events."""
        return self.root[index]


class NotificationPayload(BaseModel):
    """Payload sent to notification channels."""

    event_type: str
    event_message: str
    tailnet: str
    timestamp: datetime
    raw_data: dict[str, Any]

    @classmethod
    def from_tailscale_event(cls, event: TailscaleEvent) -> "NotificationPayload":
        """Create notification payload from Tailscale event."""
        return cls(
            event_type=event.type,
            event_message=event.message,
            tailnet=event.tailnet,
            timestamp=event.timestamp,
            raw_data=event.data,
        )
