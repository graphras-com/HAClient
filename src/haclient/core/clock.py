"""Default `Clock` implementation built on the running asyncio loop.

Entities and event dispatchers schedule background coroutines through a
`Clock`. Production code uses `AsyncioClock`; tests can substitute a
no-op or recording implementation.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any

_LOGGER = logging.getLogger(__name__)


async def _await_and_log(awaitable: Awaitable[Any]) -> None:
    """Await *awaitable* and log any exception it raises."""
    try:
        await awaitable
    except Exception:  # pragma: no cover - defensive
        _LOGGER.exception("Scheduled coroutine raised")


class AsyncioClock:
    """Schedule coroutines onto the currently-running asyncio loop."""

    def loop(self) -> asyncio.AbstractEventLoop | None:
        """Return the running event loop, if any.

        Returns
        -------
        asyncio.AbstractEventLoop or None
            The active loop, or ``None`` if called outside one.
        """
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return None

    def schedule(self, coro: Awaitable[Any]) -> None:
        """Schedule *coro* on the running loop without blocking.

        Parameters
        ----------
        coro : Awaitable
            The coroutine or awaitable to run.
        """
        loop = self.loop()
        if loop is not None and loop.is_running():
            loop.create_task(_await_and_log(coro))
        else:  # pragma: no cover - only reached without a running loop
            asyncio.ensure_future(coro)
