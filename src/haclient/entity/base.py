"""Base `Entity` implementation.

Entities depend only on narrow capability ports:

* `ServiceCaller` — to invoke Home Assistant services.
* `StateStore`    — for registration and lookup.
* `Clock`         — to schedule async listener callbacks.

This decoupling means individual entities can be unit-tested without a
running `HAClient` or `aiohttp` server.
"""

from __future__ import annotations

import contextlib
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from haclient.config import ServicePolicy

if TYPE_CHECKING:
    from haclient.core.services import ServiceCaller
    from haclient.core.state import StateStore
    from haclient.ports import Clock

_LOGGER = logging.getLogger(__name__)

StateChangeHandler = Callable[[dict[str, Any] | None, dict[str, Any] | None], Any]
"""Callback signature for full-state-dict listeners."""

ValueChangeHandler = Callable[[Any, Any], Any]
"""Callback signature for ``(old_value, new_value)`` listeners."""

F = TypeVar("F", bound=StateChangeHandler)
V = TypeVar("V", bound=ValueChangeHandler)


class Entity:
    """Represent a single Home Assistant entity.

    Subclasses target specific HA domains and add domain-specific
    methods. The ``state`` string and ``attributes`` dict reflect the
    most recent state seen by the client. They are refreshed
    automatically when the `StateStore` receives ``state_changed``
    events for this entity.

    Parameters
    ----------
    entity_id : str
        Fully-qualified entity id (e.g. ``"light.kitchen"``).
    services : ServiceCaller
        Service-call port used to invoke HA services.
    store : StateStore
        State store the entity registers itself with.
    clock : Clock
        Scheduler used to dispatch async listeners.

    Attributes
    ----------
    entity_id : str
        The fully-qualified entity id.
    state : str
        Current state string.
    attributes : dict
        Current entity attributes from Home Assistant.

    Raises
    ------
    ValueError
        If *entity_id* is not fully qualified (i.e. lacks a domain
        prefix like ``"light."``).
    """

    domain: ClassVar[str] = ""

    def __init__(
        self,
        entity_id: str,
        services: ServiceCaller,
        store: StateStore,
        clock: Clock,
    ) -> None:
        if "." not in entity_id:
            raise ValueError(
                f"entity_id must be fully qualified (e.g. 'light.kitchen'), got: {entity_id!r}"
            )
        self.entity_id: str = entity_id
        self._services: ServiceCaller = services
        self._store: StateStore = store
        self._clock: Clock = clock
        self.state: str = "unknown"
        self.attributes: dict[str, Any] = {}
        self._listeners: list[StateChangeHandler] = []
        self._attr_listeners: dict[str, list[ValueChangeHandler]] = {}
        self._state_transition_listeners: dict[str, list[ValueChangeHandler]] = {}
        self._state_value_listeners: list[ValueChangeHandler] = []
        store.register(self)

    # -- State application & dispatch ---------------------------------

    def _apply_state(self, state_obj: dict[str, Any] | None) -> None:
        """Replace the local state from a raw HA state object.

        Parameters
        ----------
        state_obj : dict or None
            The state dict from Home Assistant, or ``None`` to mark the
            entity as unavailable.
        """
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
        """Apply a state transition and dispatch listeners."""
        self._apply_state(new_state)
        for listener in list(self._listeners):
            self._schedule(listener, old_state, new_state)
        self._dispatch_granular_events(old_state, new_state)

    def _dispatch_granular_events(
        self,
        old_state: dict[str, Any] | None,
        new_state: dict[str, Any] | None,
    ) -> None:
        """Dispatch attribute and state-transition listeners."""
        old_state_str = (old_state or {}).get("state")
        new_state_str = (new_state or {}).get("state")
        old_attrs = (old_state or {}).get("attributes") or {}
        new_attrs = (new_state or {}).get("attributes") or {}

        if old_state_str != new_state_str:
            for listener in list(self._state_value_listeners):
                self._schedule_value(listener, old_state_str, new_state_str)

        if old_state_str != new_state_str and new_state_str is not None:
            for listener in list(self._state_transition_listeners.get(new_state_str, [])):
                self._schedule_value(listener, old_state_str, new_state_str)

        for attr_key, listeners in self._attr_listeners.items():
            old_val = old_attrs.get(attr_key)
            new_val = new_attrs.get(attr_key)
            if old_val != new_val:
                for listener in list(listeners):
                    self._schedule_value(listener, old_val, new_val)

    # -- Scheduling helpers -------------------------------------------

    def _schedule(
        self,
        handler: StateChangeHandler,
        old_state: dict[str, Any] | None,
        new_state: dict[str, Any] | None,
    ) -> None:
        """Invoke a state-dict handler, scheduling coroutines via the clock."""
        try:
            result = handler(old_state, new_state)
        except Exception:  # pragma: no cover - defensive
            _LOGGER.exception("State change handler raised synchronously")
            return
        if inspect.isawaitable(result):
            awaitable: Awaitable[Any] = result
            self._clock.schedule(awaitable)

    def _schedule_value(
        self,
        handler: ValueChangeHandler,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Invoke a value-change handler, scheduling coroutines via the clock."""
        try:
            result = handler(old_value, new_value)
        except Exception:
            _LOGGER.exception("Value change handler raised synchronously")
            return
        if inspect.isawaitable(result):
            awaitable: Awaitable[Any] = result
            self._clock.schedule(awaitable)

    # -- Listener registration ----------------------------------------

    def _register_attr_listener(self, attr_key: str, func: V) -> V:
        """Register a listener for changes to a specific attribute."""
        self._attr_listeners.setdefault(attr_key, []).append(func)
        return func

    def _register_state_transition_listener(self, to_state: str, func: V) -> V:
        """Register a listener for transitions *to* a specific state."""
        self._state_transition_listeners.setdefault(to_state, []).append(func)
        return func

    def _register_state_value_listener(self, func: V) -> V:
        """Register a listener for any state string change."""
        self._state_value_listeners.append(func)
        return func

    def remove_granular_listener(self, func: ValueChangeHandler) -> None:
        """Remove a previously registered granular listener.

        Searches attribute listeners, state-transition listeners, and
        state-value listeners (in that order) for *func* and removes the
        first match. Unknown handlers are silently ignored.

        Parameters
        ----------
        func : ValueChangeHandler
            The exact handler previously registered via one of the
            ``on_*`` listener methods.
        """
        for listeners in self._attr_listeners.values():
            with contextlib.suppress(ValueError):
                listeners.remove(func)
                return
        for listeners in self._state_transition_listeners.values():
            with contextlib.suppress(ValueError):
                listeners.remove(func)
                return
        with contextlib.suppress(ValueError):
            self._state_value_listeners.remove(func)

    def on_state_change(self, func: F) -> F:
        """Register *func* as a listener for raw state changes.

        Parameters
        ----------
        func : callable
            Callable invoked with ``(old_state_dict, new_state_dict)``
            on every ``state_changed`` event for this entity. May be
            sync or async.

        Returns
        -------
        callable
            The same *func*, returned so the method can be used as a
            decorator.
        """
        self._listeners.append(func)
        return func

    def remove_listener(self, func: StateChangeHandler) -> None:
        """Remove a previously registered state change listener.

        Parameters
        ----------
        func : StateChangeHandler
            The exact handler previously passed to `on_state_change`.
            Unknown handlers are silently ignored.
        """
        with contextlib.suppress(ValueError):
            self._listeners.remove(func)

    # -- State conveniences -------------------------------------------

    @property
    def available(self) -> bool:
        """Return ``True`` if the entity is currently available."""
        return self.state not in {"unavailable", "unknown"}

    async def async_refresh(self) -> None:
        """Fetch the latest state for this entity from REST."""
        state = await self._store.rest.get_state(self.entity_id)
        self._apply_state(state)

    # -- Service calls ------------------------------------------------

    async def _call_service(
        self,
        service: str,
        data: dict[str, Any] | None = None,
        *,
        domain: str | None = None,
        prefer: ServicePolicy | None = None,
    ) -> Any:
        """Invoke a service targeting this entity.

        ``entity_id`` is injected automatically.

        Parameters
        ----------
        service : str
            The service name within the entity's domain.
        data : dict or None, optional
            Additional service data.
        domain : str or None, optional
            Override domain (defaults to ``self.domain``).
        prefer : ServicePolicy or None, optional
            Per-call policy override.
        """
        payload: dict[str, Any] = {"entity_id": self.entity_id}
        if data:
            payload.update(data)
        return await self._services.call(domain or self.domain, service, payload, prefer=prefer)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.entity_id} state={self.state!r}>"
