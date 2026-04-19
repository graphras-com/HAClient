"""``light`` domain implementation."""

from __future__ import annotations

from typing import Any

from ..entity import Entity


class Light(Entity):
    """A Home Assistant light entity."""

    domain = "light"

    # ------------------------------------------------------------------ state
    @property
    def is_on(self) -> bool:
        """``True`` if the light is currently on."""
        return self.state == "on"

    @property
    def brightness(self) -> int | None:
        """Current brightness (0–255) or ``None`` if unsupported/unknown."""
        value = self.attributes.get("brightness")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Current RGB color tuple or ``None``."""
        value = self.attributes.get("rgb_color")
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return (int(value[0]), int(value[1]), int(value[2]))
        return None

    # ------------------------------------------------------------------ actions
    async def turn_on(
        self,
        *,
        brightness: int | None = None,
        rgb_color: tuple[int, int, int] | list[int] | None = None,
        color_temp: int | None = None,
        transition: float | None = None,
        **extra: Any,
    ) -> None:
        """Turn the light on, optionally setting brightness/color/transition."""
        data: dict[str, Any] = dict(extra)
        if brightness is not None:
            data["brightness"] = int(brightness)
        if rgb_color is not None:
            data["rgb_color"] = list(rgb_color)
        if color_temp is not None:
            data["color_temp"] = int(color_temp)
        if transition is not None:
            data["transition"] = transition
        await self.call_service("turn_on", data or None)

    async def turn_off(self, *, transition: float | None = None) -> None:
        """Turn the light off."""
        data: dict[str, Any] = {}
        if transition is not None:
            data["transition"] = transition
        await self.call_service("turn_off", data or None)

    async def toggle(self) -> None:
        """Toggle the on/off state of the light."""
        await self.call_service("toggle")
