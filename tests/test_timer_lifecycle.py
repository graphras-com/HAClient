"""Tests for Timer auto-create and delete lifecycle."""

from __future__ import annotations

from haclient import HAClient

from .fake_ha import FakeHA


async def test_timer_start_auto_creates_when_unknown(client: HAClient, fake_ha: FakeHA) -> None:
    """Calling start() on a timer with state 'unknown' should send timer/create first."""
    t = client.timer("my_timer")
    assert t.state == "unknown"

    await t.start(duration="00:00:10")

    # The timer/create command should have been sent (check ws_service_calls
    # won't capture it — we need to check via the call_service call that followed).
    # The call_service for timer.start should be present.
    assert len(fake_ha.ws_service_calls) == 1
    call = fake_ha.ws_service_calls[0]
    assert call["domain"] == "timer"
    assert call["service"] == "start"
    assert t._ensured is True


async def test_timer_start_skips_create_when_state_known(client: HAClient, fake_ha: FakeHA) -> None:
    """If the timer already has a state from HA, _ensure_exists is a no-op."""
    t = client.timer("my_timer")
    # Simulate that HA already reported the entity's state.
    t._apply_state({"state": "idle", "attributes": {"duration": "0:01:00"}})
    assert t.state == "idle"

    await t.start(duration="00:00:10")

    # Only the service call, no timer/create.
    assert len(fake_ha.ws_service_calls) == 1
    call = fake_ha.ws_service_calls[0]
    assert call["domain"] == "timer"
    assert call["service"] == "start"


async def test_timer_ensure_exists_only_called_once(client: HAClient, fake_ha: FakeHA) -> None:
    """After the first _ensure_exists succeeds, subsequent calls are no-ops."""
    t = client.timer("my_timer")
    assert t.state == "unknown"

    await t.start(duration="00:00:10")
    await t.pause()

    # Both actions should fire, but timer/create only once.
    assert len(fake_ha.ws_service_calls) == 2
    assert t._ensured is True


async def test_timer_pause_auto_creates(client: HAClient, fake_ha: FakeHA) -> None:
    """pause() should also trigger auto-create."""
    t = client.timer("my_timer")
    await t.pause()
    assert t._ensured is True
    assert len(fake_ha.ws_service_calls) == 1


async def test_timer_cancel_auto_creates(client: HAClient, fake_ha: FakeHA) -> None:
    """cancel() should also trigger auto-create."""
    t = client.timer("my_timer")
    await t.cancel()
    assert t._ensured is True


async def test_timer_finish_auto_creates(client: HAClient, fake_ha: FakeHA) -> None:
    """finish() should also trigger auto-create."""
    t = client.timer("my_timer")
    await t.finish()
    assert t._ensured is True


async def test_timer_change_auto_creates(client: HAClient, fake_ha: FakeHA) -> None:
    """change() should also trigger auto-create."""
    t = client.timer("my_timer")
    await t.change(duration="00:00:30")
    assert t._ensured is True


async def test_timer_delete(client: HAClient, fake_ha: FakeHA) -> None:
    """delete() sends timer/delete and resets _ensured."""
    t = client.timer("my_timer")
    # First ensure it exists.
    await t.start()
    assert t._ensured is True

    await t.delete()
    assert t._ensured is False


async def test_timer_delete_then_start_recreates(client: HAClient, fake_ha: FakeHA) -> None:
    """After delete(), the next action should re-create the timer."""
    t = client.timer("my_timer")
    await t.start()
    assert t._ensured is True

    await t.delete()
    assert t._ensured is False

    # Reset state to unknown to simulate the entity being gone.
    t.state = "unknown"
    await t.start()
    assert t._ensured is True
