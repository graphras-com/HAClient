"""Blocking / synchronous usage via :class:`SyncHAClient`.

Run this from a regular script without having to think about ``asyncio``:
it is particularly handy in REPL sessions and quick automation scripts.
"""

from __future__ import annotations

import os

from haclient import SyncHAClient


def main() -> None:
    url = os.environ["HA_URL"]
    token = os.environ["HA_TOKEN"]

    with SyncHAClient(url, token=token) as ha:
        player = ha.media_player("livingroom")
        player.play()
        player.set_volume(0.3)


if __name__ == "__main__":
    main()
