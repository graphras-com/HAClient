"""``switch`` domain implementation."""

from __future__ import annotations

from typing import Any

from haclient.core.plugins import DomainSpec, register_domain
from haclient.entity.base import Entity


class Switch(Entity):
    """A Home Assistant switch entity.

    Switches are binary devices that can be turned on or off. The public
    API uses ``on()`` / ``off()`` / ``toggle()`` as intent-specific names
    rather than the raw HA ``turn_on`` / ``turn_off`` service names.
    """

    domain = "switch"

    # -- Listener decorators ------------------------------------------

    def on_turn_on(self, func: Any) -> Any:
        """Register a listener for when the switch turns on."""
        return self._register_state_transition_listener("on", func)

    def on_turn_off(self, func: Any) -> Any:
        """Register a listener for when the switch turns off."""
        return self._register_state_transition_listener("off", func)

    # -- State properties ---------------------------------------------

    @property
    def is_on(self) -> bool:
        """Whether the switch is currently on."""
        return self.state == "on"

    # -- Actions ------------------------------------------------------

    async def on(self) -> None:
        """Activate the switch."""
        await self._call_service("turn_on")

    async def off(self) -> None:
        """Deactivate the switch."""
        await self._call_service("turn_off")

    async def toggle(self) -> None:
        """Toggle the switch state."""
        await self._call_service("toggle")


SPEC: DomainSpec[Switch] = register_domain(DomainSpec(name="switch", entity_cls=Switch))
"""The `DomainSpec` registered with the shared `DomainRegistry`."""
