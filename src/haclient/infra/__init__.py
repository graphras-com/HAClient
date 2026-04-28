"""Infrastructure adapters implementing the transport ports.

Adapters in this package depend on third-party libraries (currently
``aiohttp``). Nothing in `haclient.core` imports from here; wiring is
done by `HAClient`.
"""

from haclient.infra.rest_aiohttp import AiohttpRestAdapter
from haclient.infra.ws_aiohttp import AiohttpWebSocketAdapter

__all__ = ["AiohttpRestAdapter", "AiohttpWebSocketAdapter"]
