"""Ports — protocol definitions decoupling the core from infrastructure.

The core services and domain code depend only on these protocols. Concrete
implementations (e.g. aiohttp-based REST and WebSocket clients) live under
`haclient.infra` and are wired in by `HAClient`. This is the hexagonal
boundary: infrastructure adapters implement these ports; nothing in the
core layer imports from `haclient.infra`.

Notes
-----
The protocols intentionally describe a minimal surface. Adapters may
expose additional helpers, but the core promises only to use what is
declared here.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]
"""Callable invoked with a single Home Assistant event payload."""

DisconnectListener = Callable[[], Awaitable[None] | None]
"""Callable invoked when the WebSocket connection drops."""

ReconnectListener = Callable[[], Awaitable[None] | None]
"""Callable invoked after a successful WebSocket reconnect."""


@runtime_checkable
class RestPort(Protocol):
    """REST transport contract used by the core.

    Implementations talk to the Home Assistant ``/api/`` HTTP endpoints.
    """

    @property
    def base_url(self) -> str:
        """Return the configured Home Assistant base URL."""
        ...

    async def get_states(self) -> list[dict[str, Any]]:
        """Return all current entity states."""
        ...

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        """Return a single entity state, or ``None`` if not found."""
        ...

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Invoke a Home Assistant service via the REST API."""
        ...

    async def close(self) -> None:
        """Release any resources owned by the adapter."""
        ...


@runtime_checkable
class WebSocketPort(Protocol):
    """WebSocket transport contract used by the core.

    Implementations talk to the Home Assistant ``/api/websocket`` endpoint
    and handle authentication, reconnect, and event subscription.
    """

    @property
    def connected(self) -> bool:
        """``True`` while the underlying socket is open."""
        ...

    async def connect(self) -> None:
        """Open the connection and authenticate."""
        ...

    async def close(self) -> None:
        """Close the connection and stop background tasks."""
        ...

    async def send_command(
        self,
        payload: dict[str, Any],
        *,
        timeout: float | None = None,
    ) -> Any:
        """Send a command and await its response."""
        ...

    async def subscribe_events(
        self,
        handler: EventHandler,
        event_type: str | None = None,
    ) -> int:
        """Subscribe to a Home Assistant event stream."""
        ...

    async def unsubscribe(self, subscription_id: int) -> None:
        """Cancel a previously registered subscription."""
        ...

    def on_disconnect(self, handler: DisconnectListener) -> DisconnectListener:
        """Register a listener for connection drops."""
        ...

    def on_reconnect(self, handler: ReconnectListener) -> ReconnectListener:
        """Register a listener for successful reconnections."""
        ...


@runtime_checkable
class Clock(Protocol):
    """Loop / scheduling contract used by entities and event dispatchers.

    Decouples scheduling of background coroutines from the concrete event
    loop, which makes it easy to substitute during testing.
    """

    def loop(self) -> asyncio.AbstractEventLoop | None:
        """Return the running event loop, or ``None`` if unavailable."""
        ...

    def schedule(self, coro: Awaitable[Any]) -> None:
        """Run *coro* on the loop without blocking the caller."""
        ...
