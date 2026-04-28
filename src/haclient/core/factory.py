"""`EntityFactory` — instantiates entities lazily for a given `DomainSpec`.

The factory binds the four "narrow ports" each entity needs (services,
state store, clock, plus the spec-defined event subscription) and
short-circuits to the existing instance when one is already registered.

Type-conflict checks (e.g. trying to obtain a `Light` for an entity id
already registered as a `Switch`) raise `HAClientError`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from haclient.core.plugins import DomainSpec, EntityFactoryProtocol
from haclient.exceptions import HAClientError
from haclient.ports import Clock

if TYPE_CHECKING:
    from haclient.core.services import ServiceCaller
    from haclient.core.state import StateStore
    from haclient.entity.base import Entity

_LOGGER = logging.getLogger(__name__)


class EntityFactory(EntityFactoryProtocol):
    """Create or fetch entities according to a `DomainSpec`."""

    def __init__(
        self,
        services: ServiceCaller,
        state: StateStore,
        clock: Clock,
    ) -> None:
        self._services = services
        self._state = state
        self._clock = clock

    @property
    def services(self) -> ServiceCaller:
        """Return the bound `ServiceCaller`."""
        return self._services

    @property
    def state(self) -> StateStore:
        """Return the bound `StateStore`."""
        return self._state

    @property
    def clock(self) -> Clock:
        """Return the bound `Clock`."""
        return self._clock

    def get_or_create(self, spec: DomainSpec[Any], name: str) -> Any:
        """Return the entity for ``spec.name + '.' + name``.

        Parameters
        ----------
        spec : DomainSpec
            The spec describing the domain.
        name : str
            Short object-id (no dot allowed).

        Returns
        -------
        Entity
            The existing or newly created entity.

        Raises
        ------
        HAClientError
            If an entity with the resolved id already exists but is
            registered with a different class than ``spec.entity_cls``.
        """
        entity_id = self._state.registry.resolve(spec.name, name)
        existing = self._state.registry.get(entity_id)
        if existing is not None:
            if not isinstance(existing, spec.entity_cls):
                raise HAClientError(
                    f"Entity {entity_id} is registered as "
                    f"{type(existing).__name__}, not {spec.entity_cls.__name__}"
                )
            return existing
        entity = spec.entity_cls(entity_id, self._services, self._state, self._clock)
        return entity

    def in_domain(self, spec: DomainSpec[Any]) -> list[Entity]:
        """Return all currently registered entities for *spec*."""
        return self._state.registry.in_domain(spec.name)
