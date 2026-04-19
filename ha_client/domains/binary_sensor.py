"""``binary_sensor`` domain implementation (read-only)."""

from __future__ import annotations

from ..entity import Entity


class BinarySensor(Entity):
    """A read-only Home Assistant binary sensor entity."""

    domain = "binary_sensor"

    @property
    def is_on(self) -> bool:
        """``True`` if the binary sensor is in the ``on`` state."""
        return self.state == "on"

    @property
    def device_class(self) -> str | None:
        """The device class (e.g. ``"motion"``, ``"door"``)."""
        value = self.attributes.get("device_class")
        return str(value) if value is not None else None
