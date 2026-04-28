"""`StateStore` — entity registry plus state priming and refresh.

Owns the `EntityRegistry` and the logic that:

1. Subscribes to ``state_changed`` first (with buffering enabled).
2. Pulls the REST snapshot and applies it to registered entities.
3. Drains the buffered events so any state transitions that occurred
   between subscribe and snapshot are applied in order.

This sequence eliminates the connect-time race where events between the
REST snapshot and the live event stream would be lost. The same priming
runs after a reconnect so post-reconnect state is also reconciled.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from haclient.core.events import EventBus
from haclient.core.registry import EntityRegistry
from haclient.exceptions import HAClientError
from haclient.ports import RestPort

if TYPE_CHECKING:
    from haclient.entity.base import Entity

_LOGGER = logging.getLogger(__name__)

STATE_CHANGED = "state_changed"


class StateStore:
    """Registry of entities plus priming and refresh of their state.

    Parameters
    ----------
    rest : RestPort
        REST adapter used for state snapshots.
    events : EventBus
        Event bus used to receive ``state_changed`` events.
    registry : EntityRegistry or None, optional
        Existing registry instance. A new one is created when omitted.
    """

    def __init__(
        self,
        rest: RestPort,
        events: EventBus,
        *,
        registry: EntityRegistry | None = None,
    ) -> None:
        self._rest = rest
        self._events = events
        self._registry = registry or EntityRegistry()
        events.subscribe(STATE_CHANGED, self._on_state_changed)

    @property
    def registry(self) -> EntityRegistry:
        """Return the underlying `EntityRegistry`."""
        return self._registry

    @property
    def rest(self) -> RestPort:
        """Return the REST adapter used for snapshots and refreshes."""
        return self._rest

    def register(self, entity: Entity) -> None:
        """Register *entity* in the underlying registry."""
        self._registry.register(entity)

    def get(self, entity_id: str) -> Entity | None:
        """Return the entity with *entity_id* if known."""
        return self._registry.get(entity_id)

    def __iter__(self) -> Iterator[Entity]:
        return iter(self._registry)

    async def prime(self) -> None:
        """Subscribe to ``state_changed`` then reconcile with a REST snapshot.

        The buffer captures events that arrive between the subscription
        confirmation and the REST snapshot. After applying the snapshot
        the buffer is drained, applying every captured event in order.
        Replays are idempotent because `_apply_state` does a full
        replacement.
        """
        self._events.enable_buffering(STATE_CHANGED)
        await self._events.start()
        try:
            states = await self._rest.get_states()
        except HAClientError as err:
            _LOGGER.warning("Initial state fetch failed: %s", err)
            self._events.discard_buffer(STATE_CHANGED)
            return
        for state in states:
            eid = state.get("entity_id") if isinstance(state, dict) else None
            if not isinstance(eid, str):
                continue
            entity = self._registry.get(eid)
            if entity is not None:
                entity._apply_state(state)  # noqa: SLF001
        await self._events.drain_buffer(STATE_CHANGED)

    async def refresh_all(self) -> None:
        """Refresh every registered entity from the REST API."""
        states = await self._rest.get_states()
        index: dict[str, dict[str, Any]] = {}
        for state in states:
            if not isinstance(state, dict):
                continue
            eid = state.get("entity_id")
            if isinstance(eid, str):
                index[eid] = state
        for entity in list(self._registry):
            entity._apply_state(index.get(entity.entity_id))  # noqa: SLF001

    def _on_state_changed(self, event: dict[str, Any]) -> None:
        """Apply a single ``state_changed`` event to its target entity."""
        data = event.get("data") or {}
        eid = data.get("entity_id")
        if not isinstance(eid, str):
            return
        entity = self._registry.get(eid)
        if entity is None:
            return
        entity._handle_state_changed(  # noqa: SLF001
            data.get("old_state"), data.get("new_state")
        )
