"""Core services: connection, events, services, state, registry, plugins.

This subpackage is transport-agnostic. It depends only on `haclient.ports`,
`haclient.config`, and `haclient.exceptions` — never on `haclient.infra`
or `haclient.domains`.
"""

from haclient.core.clock import AsyncioClock
from haclient.core.connection import Connection
from haclient.core.events import EventBus
from haclient.core.factory import EntityFactory
from haclient.core.plugins import DomainAccessor, DomainRegistry, DomainSpec, register_domain
from haclient.core.registry import EntityRegistry
from haclient.core.services import ServiceCaller
from haclient.core.state import StateStore

__all__ = [
    "AsyncioClock",
    "Connection",
    "DomainAccessor",
    "DomainRegistry",
    "DomainSpec",
    "EntityFactory",
    "EntityRegistry",
    "EventBus",
    "ServiceCaller",
    "StateStore",
    "register_domain",
]
