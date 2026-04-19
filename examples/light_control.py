"""Turn on a Home Assistant light with specific brightness/colour."""

from __future__ import annotations

import asyncio
import os

from ha_client import HAClient


async def main() -> None:
    url = os.environ["HA_URL"]
    token = os.environ["HA_TOKEN"]

    async with HAClient(url, token=token) as ha:
        light = ha.light("kitchen")
        await light.turn_on(brightness=180, rgb_color=(255, 160, 0), transition=1.5)
        await asyncio.sleep(2)
        await light.turn_off(transition=1.5)


if __name__ == "__main__":
    asyncio.run(main())
