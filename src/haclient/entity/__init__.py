"""Entity base classes.

This subpackage hosts the transport-agnostic `Entity` used by all
domain-specific subclasses. Entities depend only on the narrow ports
(`ServiceCaller`, `StateStore`, `Clock`) — never on the full `HAClient`.
"""

from haclient.entity.base import Entity, StateChangeHandler, ValueChangeHandler

__all__ = ["Entity", "StateChangeHandler", "ValueChangeHandler"]
