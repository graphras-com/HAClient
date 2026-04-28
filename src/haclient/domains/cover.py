"""``cover`` domain implementation."""

from __future__ import annotations

from typing import Any

from haclient.core.plugins import DomainSpec, register_domain
from haclient.entity.base import Entity


class Cover(Entity):
    """A Home Assistant cover (blind/garage/shade) entity.

    Uses intent-specific names (``open``, ``close``, ``stop``,
    ``set_position``) rather than raw HA service names.
    """

    domain = "cover"

    # -- Listener decorators ------------------------------------------

    def on_open(self, func: Any) -> Any:
        """Register a listener for when the cover opens."""
        return self._register_state_transition_listener("open", func)

    def on_close(self, func: Any) -> Any:
        """Register a listener for when the cover closes."""
        return self._register_state_transition_listener("closed", func)

    def on_position_change(self, func: Any) -> Any:
        """Register a listener for position changes."""
        return self._register_attr_listener("current_position", func)

    # -- State properties ---------------------------------------------

    @property
    def is_open(self) -> bool:
        """Whether the cover is currently open."""
        return self.state == "open"

    @property
    def is_closed(self) -> bool:
        """Whether the cover is currently closed."""
        return self.state == "closed"

    @property
    def current_position(self) -> int | None:
        """Current position (0--100) or ``None`` if unsupported."""
        value = self.attributes.get("current_position")
        return int(value) if isinstance(value, (int, float)) else None

    # -- Actions ------------------------------------------------------

    async def open(self) -> None:
        """Open the cover fully."""
        await self._call_service("open_cover")

    async def close(self) -> None:
        """Close the cover fully."""
        await self._call_service("close_cover")

    async def stop(self) -> None:
        """Stop movement of the cover."""
        await self._call_service("stop_cover")

    async def set_position(self, position: int) -> None:
        """Set the cover position (0 = closed, 100 = open)."""
        await self._call_service("set_cover_position", {"position": int(position)})

    async def toggle(self) -> None:
        """Toggle open/close state."""
        await self._call_service("toggle")


SPEC: DomainSpec[Cover] = register_domain(DomainSpec(name="cover", entity_cls=Cover))
"""The `DomainSpec` registered with the shared `DomainRegistry`."""
