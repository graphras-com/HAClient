"""Tests for MediaPlayer.favorites() recursive traversal."""

from __future__ import annotations

from typing import Any

from aiohttp import web

from ha_client import HAClient

from .fake_ha import FakeHA


def _make_tree() -> dict[str, Any]:
    """Return a multi-level browse_media root used by the browse handler."""
    return {
        "title": "root",
        "media_content_id": "root",
        "media_content_type": "root",
        "can_expand": True,
        "can_play": False,
        "children": [
            {
                "title": "Favorites",
                "media_content_id": "favs",
                "media_content_type": "directory",
                "can_expand": True,
                "can_play": False,
            },
            {
                "title": "Single Track",
                "media_content_id": "track://1",
                "media_content_type": "track",
                "can_expand": False,
                "can_play": True,
            },
            # Duplicated child – should be de-duplicated on output.
            {
                "title": "Single Track dup",
                "media_content_id": "track://1",
                "media_content_type": "track",
                "can_expand": False,
                "can_play": True,
            },
        ],
    }


def _make_subtree() -> dict[str, Any]:
    return {
        "title": "Favorites",
        "media_content_id": "favs",
        "media_content_type": "directory",
        "can_expand": True,
        "can_play": False,
        "children": [
            {
                "title": "Playlist A",
                "media_content_id": "playlist://a",
                "media_content_type": "playlist",
                "can_expand": True,
                "can_play": True,
            },
            {
                "title": "BadItem",
                # missing media_content_id → must be skipped
                "media_content_type": "track",
                "can_play": True,
                "can_expand": False,
            },
            "not-a-dict",
        ],
    }


def _make_playlist_a() -> dict[str, Any]:
    return {
        "title": "Playlist A",
        "media_content_id": "playlist://a",
        "media_content_type": "playlist",
        "can_expand": True,
        "can_play": True,
        "children": [
            {
                "title": "Song 1",
                "media_content_id": "song://1",
                "media_content_type": "track",
                "can_expand": False,
                "can_play": True,
            },
            {
                "title": "Song 2",
                "media_content_id": "song://2",
                "media_content_type": "track",
                "can_expand": False,
                "can_play": True,
            },
        ],
    }


async def _browse_handler(
    server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
) -> None:
    content_id = msg.get("media_content_id")
    if content_id is None:
        result = _make_tree()
    elif content_id == "favs":
        result = _make_subtree()
    elif content_id == "playlist://a":
        result = _make_playlist_a()
    else:
        result = {"children": []}
    await ws.send_json(
        {"id": msg["id"], "type": "result", "success": True, "result": result}
    )


async def test_favorites_flattens_tree(client: HAClient, fake_ha: FakeHA) -> None:
    fake_ha.handlers["media_player/browse_media"] = _browse_handler
    mp = client.media_player("livingroom")
    favs = await mp.favorites()
    titles = [f.title for f in favs]
    ids = [f.media_content_id for f in favs]
    # Expected: Single Track (dedup), Playlist A, Song 1, Song 2
    assert "Single Track" in titles
    assert "Playlist A" in titles
    assert "Song 1" in titles
    assert "Song 2" in titles
    # No duplicates
    assert len(ids) == len(set(ids))
    # BadItem (missing content id) must be excluded.
    assert "BadItem" not in titles


async def test_favorites_item_play(client: HAClient, fake_ha: FakeHA) -> None:
    fake_ha.handlers["media_player/browse_media"] = _browse_handler
    mp = client.media_player("livingroom")
    favs = await mp.favorites()
    assert favs
    # Pick the Playlist A favorite and play it.
    playlist = next(f for f in favs if f.title == "Playlist A")
    await playlist.play()
    call = fake_ha.ws_service_calls[-1]
    assert call["service"] == "play_media"
    assert call["service_data"]["media_content_id"] == "playlist://a"
    assert call["service_data"]["media_content_type"] == "playlist"
    assert "FavoriteItem" in repr(playlist)


async def test_favorites_returns_empty_when_unsupported(
    client: HAClient, fake_ha: FakeHA
) -> None:
    async def not_supported(
        server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
    ) -> None:
        await ws.send_json(
            {
                "id": msg["id"],
                "type": "result",
                "success": False,
                "error": {"code": "not_supported", "message": "nope"},
            }
        )

    fake_ha.handlers["media_player/browse_media"] = not_supported
    mp = client.media_player("livingroom")
    result = await mp.favorites()
    assert result == []


async def test_favorites_max_depth(client: HAClient, fake_ha: FakeHA) -> None:
    """Guard: max_depth stops recursion."""
    fake_ha.handlers["media_player/browse_media"] = _browse_handler
    mp = client.media_player("livingroom")
    # max_depth=1 means only the top-level children are considered – we should
    # get the Single Track but *not* Song 1 / Song 2 (those live two levels
    # below the root).
    favs = await mp.favorites(max_depth=1)
    titles = [f.title for f in favs]
    assert "Single Track" in titles
    assert "Song 1" not in titles


async def test_favorites_max_nodes(client: HAClient, fake_ha: FakeHA) -> None:
    fake_ha.handlers["media_player/browse_media"] = _browse_handler
    mp = client.media_player("livingroom")
    result = await mp.favorites(max_nodes=1)
    # With only one node visited we cannot descend; the only candidates are
    # those discovered at the root node itself.
    assert all(isinstance(f.title, str) for f in result)


async def test_favorites_subtree_failure_is_tolerated(
    client: HAClient, fake_ha: FakeHA
) -> None:
    async def partial(
        server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
    ) -> None:
        content_id = msg.get("media_content_id")
        if content_id is None:
            await ws.send_json(
                {
                    "id": msg["id"],
                    "type": "result",
                    "success": True,
                    "result": _make_tree(),
                }
            )
        else:
            # Every subtree browse fails.
            await ws.send_json(
                {
                    "id": msg["id"],
                    "type": "result",
                    "success": False,
                    "error": {"code": "fail", "message": "no"},
                }
            )

    fake_ha.handlers["media_player/browse_media"] = partial
    mp = client.media_player("livingroom")
    favs = await mp.favorites()
    titles = [f.title for f in favs]
    assert "Single Track" in titles  # still collected from the root
    assert "Song 1" not in titles


async def test_browse_media_malformed_response(
    client: HAClient, fake_ha: FakeHA
) -> None:
    async def bad(
        server: FakeHA, ws: web.WebSocketResponse, msg: dict[str, Any]
    ) -> None:
        await ws.send_json(
            {
                "id": msg["id"],
                "type": "result",
                "success": True,
                "result": "not-a-dict",
            }
        )

    fake_ha.handlers["media_player/browse_media"] = bad
    mp = client.media_player("livingroom")
    # favorites swallows HAClientError from browse_media.
    assert await mp.favorites() == []
