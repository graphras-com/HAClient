"""Control a Home Assistant media player.

Usage:

    HA_URL=http://ha.local:8123 HA_TOKEN=xxxxxxxx python examples/media_player.py
"""

from __future__ import annotations

import asyncio
import os

from haclient import HAClient


async def main() -> None:
    url = os.environ["HA_URL"]
    token = os.environ["HA_TOKEN"]

    async with HAClient(url, token=token) as ha:
        player = ha.media_player("livingroom")
        await player.async_refresh()
        print(f"State: {player.state}  volume={player.volume_level}")

        await player.play()
        await asyncio.sleep(1)
        await player.set_volume(0.4)
        await asyncio.sleep(1)
        await player.next()


if __name__ == "__main__":
    asyncio.run(main())
