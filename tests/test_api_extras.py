"""Targeted coverage for `HAClient` accessors and helpers."""

from __future__ import annotations

from haclient import HAClient
from haclient.config import ConnectionConfig


async def test_property_surface_round_trip() -> None:
    config = ConnectionConfig.from_url("http://x", token="t")
    ha = HAClient(config, load_plugins=False)
    try:
        assert ha.config is config
        assert ha.base_url == "http://x"
        assert ha.connection is not None
        assert ha.events is not None
        assert ha.services is not None
        assert ha.state is not None
        assert ha.domains is ha._registry  # type: ignore[attr-defined]
    finally:
        await ha.close()


async def test_event_router_ignores_unknown_entity_and_bad_id() -> None:
    """Cover the early-return branches in `_make_event_router`."""
    ha = HAClient.from_url("http://x", token="t", load_plugins=False)
    try:
        from haclient.domains.timer import SPEC as timer_spec

        route = ha._make_event_router(timer_spec)  # type: ignore[attr-defined]
        # Bad entity_id type — early return.
        route({"event_type": "timer.finished", "data": {"entity_id": 42}})
        # Unknown entity — early return.
        route({"event_type": "timer.finished", "data": {"entity_id": "timer.unknown"}})
        # Spec with no on_event — early return.
        from haclient.core.plugins import DomainSpec

        bare = DomainSpec(name="bare", entity_cls=timer_spec.entity_cls)
        bare_route = ha._make_event_router(bare)  # type: ignore[attr-defined]
        bare_route({"event_type": "x", "data": {"entity_id": "timer.x"}})
    finally:
        await ha.close()
