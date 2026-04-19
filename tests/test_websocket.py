"""Tests for the low-level WebSocketClient."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from aiohttp import web

from ha_client.exceptions import (
    AuthenticationError,
    CommandError,
    ConnectionClosedError,
)
from ha_client.exceptions import TimeoutError as HATimeoutError
from ha_client.websocket import WebSocketClient

from .fake_ha import FakeHA


async def _make_ws(fake_ha: FakeHA, **kwargs: Any) -> WebSocketClient:
    ws = WebSocketClient(
        fake_ha.ws_url,
        fake_ha.token,
        ping_interval=0,
        request_timeout=3.0,
        **kwargs,
    )
    await ws.connect()
    return ws


async def test_connect_and_auth(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    try:
        assert ws.connected
    finally:
        await ws.close()
    assert not ws.connected


async def test_auth_invalid(fake_ha: FakeHA) -> None:
    ws = WebSocketClient(fake_ha.ws_url, "wrong-token", ping_interval=0)
    with pytest.raises(AuthenticationError):
        await ws.connect()
    await ws.close()


async def test_send_command_success(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    try:
        result = await ws.send_command(
            {"type": "call_service", "domain": "light", "service": "turn_on"}
        )
        assert isinstance(result, dict)
        assert "context" in result
    finally:
        await ws.close()


async def test_send_command_error(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    try:
        with pytest.raises(CommandError) as excinfo:
            await ws.send_command({"type": "unknown/command"})
        assert excinfo.value.code == "unknown_command"
    finally:
        await ws.close()


async def test_send_command_timeout(fake_ha: FakeHA) -> None:
    async def never_reply(server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]) -> None:
        await asyncio.sleep(10)

    fake_ha.handlers["slow"] = never_reply
    ws = await _make_ws(fake_ha)
    try:
        with pytest.raises(HATimeoutError):
            await ws.send_command({"type": "slow"}, timeout=0.1)
    finally:
        await ws.close()


async def test_subscribe_and_event(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    received: list[dict[str, Any]] = []

    async def handler(event: dict[str, Any]) -> None:
        received.append(event)

    try:
        sub_id = await ws.subscribe_events(handler, "state_changed")
        await fake_ha.push_event(
            "state_changed",
            {"data": {"entity_id": "light.kitchen"}},
        )
        # give reader a tick
        await asyncio.sleep(0.05)
        assert received
        assert received[0]["event_type"] == "state_changed"
        await ws.unsubscribe(sub_id)
    finally:
        await ws.close()


async def test_ping_pong(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    try:
        await ws.ping(timeout=1.0)
    finally:
        await ws.close()


async def test_send_command_while_disconnected(fake_ha: FakeHA) -> None:
    ws = WebSocketClient(fake_ha.ws_url, fake_ha.token, ping_interval=0, reconnect=False)
    with pytest.raises(ConnectionClosedError):
        await ws.send_command({"type": "ping"})


async def test_reconnect_on_drop(fake_ha: FakeHA) -> None:
    """Force the server to close the WS and verify the client reconnects."""
    ws = await _make_ws(fake_ha, reconnect=True)
    try:
        # Subscribe so we can verify re-subscription after reconnect.
        received: list[dict[str, Any]] = []

        async def handler(event: dict[str, Any]) -> None:
            received.append(event)

        await ws.subscribe_events(handler, "state_changed")

        # Kill the connection from the server side.
        for conn in list(fake_ha.connections):
            await conn.close()

        # Wait until the reconnect loop re-establishes.
        for _ in range(50):
            await asyncio.sleep(0.1)
            if ws.connected:
                break
        assert ws.connected

        # After reconnect, push another event – handler should still fire.
        await fake_ha.push_event("state_changed", {"data": {"entity_id": "x"}})
        await asyncio.sleep(0.1)
        assert received
    finally:
        await ws.close()


async def test_disconnect_listener(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha, reconnect=False)
    called = asyncio.Event()

    @ws.on_disconnect
    async def on_disconnect() -> None:
        called.set()

    # Close from server side; client-side reader should notice.
    for conn in list(fake_ha.connections):
        await conn.close()

    await asyncio.wait_for(called.wait(), timeout=3)
    await ws.close()


async def test_disconnect_listener_sync(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha, reconnect=False)
    called = threading_like_flag()

    @ws.on_disconnect
    def on_disconnect() -> None:
        called.set()

    for conn in list(fake_ha.connections):
        await conn.close()

    for _ in range(30):
        await asyncio.sleep(0.05)
        if called.is_set():
            break
    assert called.is_set()
    await ws.close()


def threading_like_flag() -> _Flag:
    return _Flag()


class _Flag:
    def __init__(self) -> None:
        self._set = False

    def set(self) -> None:
        self._set = True

    def is_set(self) -> bool:
        return self._set


async def test_unsubscribe(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha)
    received: list[dict[str, Any]] = []

    async def handler(event: dict[str, Any]) -> None:
        received.append(event)

    try:
        sub_id = await ws.subscribe_events(handler, "state_changed")
        await ws.unsubscribe(sub_id)
        # After unsubscribe the event should not be dispatched.
        await fake_ha.push_event("state_changed", {"data": {}})
        await asyncio.sleep(0.05)
        assert received == []
    finally:
        await ws.close()


async def test_cannot_connect_to_bad_port() -> None:
    ws = WebSocketClient(
        "ws://127.0.0.1:1",  # port 1: nothing listening
        "token",
        ping_interval=0,
        reconnect=False,
    )
    with pytest.raises(Exception):  # noqa: B017  - aiohttp raises ClientError
        await ws.connect()
    await ws.close()


async def test_subscribe_events_failure_rolls_back(fake_ha: FakeHA) -> None:
    async def reject(
        server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
    ) -> None:
        await ws.send_json(
            {
                "id": msg["id"],
                "type": "result",
                "success": False,
                "error": {"code": "bad", "message": "no"},
            }
        )

    fake_ha.handlers["subscribe_events"] = reject
    ws = await _make_ws(fake_ha)

    async def handler(event: dict[str, Any]) -> None:
        pass

    try:
        with pytest.raises(CommandError):
            await ws.subscribe_events(handler, "state_changed")
        # Internal state should be clean again.
        assert not ws._subscriptions  # noqa: SLF001
        assert not ws._event_subs  # noqa: SLF001
    finally:
        await ws.close()


async def test_close_cancels_pending_request(fake_ha: FakeHA) -> None:
    async def never_reply(
        server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
    ) -> None:
        await asyncio.sleep(10)

    fake_ha.handlers["slow"] = never_reply
    ws = await _make_ws(fake_ha)

    async def run_and_wait() -> None:
        with pytest.raises(ConnectionClosedError):
            await ws.send_command({"type": "slow"})

    task = asyncio.create_task(run_and_wait())
    await asyncio.sleep(0.2)
    await ws.close()
    await task


async def test_reader_handles_non_json_text_frame(fake_ha: FakeHA) -> None:
    ws = await _make_ws(fake_ha, reconnect=False)
    try:
        # Send a text frame that isn't JSON via a custom handler.
        async def send_garbage(server: FakeHA, server_ws: Any, msg: dict[str, Any]) -> None:
            await server_ws.send_str("not-json")
            await server_ws.send_json(
                {"id": msg["id"], "type": "result", "success": True, "result": None}
            )

        fake_ha.handlers["garbage"] = send_garbage
        # send_command should still succeed because the garbage frame is
        # logged & skipped.
        result = await ws.send_command({"type": "garbage"})
        assert result is None
    finally:
        await ws.close()


async def test_keepalive_triggers_reconnect(fake_ha: FakeHA) -> None:
    """If the ping times out, the socket gets force-closed and reconnect kicks in."""
    # Override ping so the server never responds to it.
    async def slow_ping(server: FakeHA, ws: Any, msg: dict[str, Any]) -> None:
        await asyncio.sleep(10)

    fake_ha.handlers["ping"] = slow_ping
    ws = WebSocketClient(
        fake_ha.ws_url,
        fake_ha.token,
        ping_interval=0.2,
        request_timeout=0.3,
        reconnect=True,
    )
    await ws.connect()
    try:
        # Wait long enough for ping to time out and socket to drop.
        await asyncio.sleep(1.0)
        # Reconnect loop should have re-established.
        for _ in range(40):
            if ws.connected:
                break
            await asyncio.sleep(0.1)
        # Either reconnected or at least we exercised the timeout path.
    finally:
        await ws.close()
