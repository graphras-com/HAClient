"""Base :class:`Entity` implementation.

Entities are bound to an :class:`ha_client.client.HAClient` instance and
automatically receive state updates from WebSocket ``state_changed`` events.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from .client import HAClient

_LOGGER = logging.getLogger(__name__)

StateChangeHandler = Callable[[dict[str, Any] | None, dict[str, Any] | None], Any]
F = TypeVar("F", bound=StateChangeHandler)


class Entity:
    """Represents a single Home Assistant entity.

    Subclasses map to specific domains (``media_player``, ``light``, ...) and
    should override :attr:`domain` and add domain-specific methods.

    The :attr:`state` string and :attr:`attributes` dictionary reflect the most
    recent state known to the client. They are refreshed automatically when the
    client receives ``state_changed`` events for this entity.
    """

    domain: str = ""  # overridden by subclasses

    def __init__(self, entity_id: str, client: HAClient) -> None:
        if "." not in entity_id:
            raise ValueError(
                f"entity_id must be fully qualified (e.g. 'light.kitchen'), got: {entity_id!r}"
            )
        self.entity_id: str = entity_id
        self._client: HAClient = client
        self.state: str = "unknown"
        self.attributes: dict[str, Any] = {}
        self._listeners: list[StateChangeHandler] = []
        client.registry.register(self)

    # --------------------------------------------------------- state plumbing
    def _apply_state(self, state_obj: dict[str, Any] | None) -> None:
        """Apply a raw state object (as returned by Home Assistant)."""
        if state_obj is None:
            self.state = "unavailable"
            self.attributes = {}
            return
        self.state = str(state_obj.get("state", "unknown"))
        attrs = state_obj.get("attributes")
        self.attributes = dict(attrs) if isinstance(attrs, dict) else {}

    def _handle_state_changed(
        self,
        old_state: dict[str, Any] | None,
        new_state: dict[str, Any] | None,
    ) -> None:
        """Internal: update local state and dispatch listeners."""
        self._apply_state(new_state)
        for listener in list(self._listeners):
            self._schedule(listener, old_state, new_state)

    def _schedule(
        self,
        handler: StateChangeHandler,
        old_state: dict[str, Any] | None,
        new_state: dict[str, Any] | None,
    ) -> None:
        try:
            result = handler(old_state, new_state)
        except Exception:  # pragma: no cover - defensive
            _LOGGER.exception("State change handler raised synchronously")
            return
        if inspect.isawaitable(result):
            awaitable: Awaitable[Any] = result
            loop = self._client.loop
            if loop is not None and loop.is_running():
                loop.create_task(_await_and_log(awaitable))
            else:  # pragma: no cover - only reached without running loop
                asyncio.ensure_future(awaitable)

    # ------------------------------------------------------------- decorators
    def on_state_change(self, func: F) -> F:
        """Register ``func`` as a listener for state changes on this entity.

        May be used as a decorator. The callback receives the previous and new
        raw state objects (``dict`` or ``None``). Coroutine functions are fully
        supported and will be scheduled on the client's event loop without
        blocking the dispatcher.
        """
        self._listeners.append(func)
        return func

    def remove_listener(self, func: StateChangeHandler) -> None:
        """Remove a previously registered state change listener."""
        with contextlib.suppress(ValueError):
            self._listeners.remove(func)

    # ----------------------------------------------------------- convenience
    @property
    def available(self) -> bool:
        """Return ``True`` if the entity is currently available."""
        return self.state not in {"unavailable", "unknown"}

    async def async_refresh(self) -> None:
        """Fetch the latest state for this entity from the REST API."""
        state = await self._client.rest.get_state(self.entity_id)
        self._apply_state(state)

    async def call_service(
        self,
        service: str,
        data: dict[str, Any] | None = None,
        *,
        domain: str | None = None,
    ) -> Any:
        """Call a Home Assistant service targeting this entity.

        ``service`` is the service name within ``domain`` (defaulting to this
        entity's domain). ``entity_id`` is injected automatically into the
        service data.
        """
        payload: dict[str, Any] = {"entity_id": self.entity_id}
        if data:
            payload.update(data)
        return await self._client.call_service(domain or self.domain, service, payload)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.entity_id} state={self.state!r}>"


async def _await_and_log(awaitable: Awaitable[Any]) -> None:
    """Await ``awaitable`` and log any exception raised by the handler."""
    try:
        await awaitable
    except Exception:  # pragma: no cover - defensive
        _LOGGER.exception("Async state change handler raised")
