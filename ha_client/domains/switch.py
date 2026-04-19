"""``switch`` domain implementation."""

from __future__ import annotations

from ..entity import Entity


class Switch(Entity):
    """A Home Assistant switch entity."""

    domain = "switch"

    @property
    def is_on(self) -> bool:
        """``True`` if the switch is currently on."""
        return self.state == "on"

    async def turn_on(self) -> None:
        """Turn the switch on."""
        await self.call_service("turn_on")

    async def turn_off(self) -> None:
        """Turn the switch off."""
        await self.call_service("turn_off")

    async def toggle(self) -> None:
        """Toggle the switch state."""
        await self.call_service("toggle")
