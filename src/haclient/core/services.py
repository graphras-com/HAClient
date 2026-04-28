"""`ServiceCaller` — explicit WS / REST routing for service invocations.

The previous implementation chose between WebSocket and REST inside a
private helper on `HAClient`. That coupled transport policy to the
client class and made the choice invisible to callers. `ServiceCaller`
makes the policy first-class:

* The default policy is fixed at construction time.
* Each call may override the policy via the ``prefer`` parameter.

Policies
--------
* ``"ws"``   — always use the WebSocket. Fails with `ConnectionClosedError`
  if the WS is not connected.
* ``"rest"`` — always use REST.
* ``"auto"`` — prefer WebSocket when connected, otherwise fall back to REST.
"""

from __future__ import annotations

from typing import Any

from haclient.config import ServicePolicy
from haclient.exceptions import ConnectionClosedError
from haclient.ports import RestPort, WebSocketPort


class ServiceCaller:
    """Route ``call_service`` invocations between WebSocket and REST.

    Parameters
    ----------
    rest : RestPort
        Adapter implementing the REST transport.
    ws : WebSocketPort
        Adapter implementing the WebSocket transport.
    default_policy : ServicePolicy
        Default routing policy used when ``prefer`` is omitted.
    """

    def __init__(
        self,
        rest: RestPort,
        ws: WebSocketPort,
        *,
        default_policy: ServicePolicy = "auto",
    ) -> None:
        self._rest = rest
        self._ws = ws
        self._default_policy = default_policy

    @property
    def default_policy(self) -> ServicePolicy:
        """Return the default routing policy."""
        return self._default_policy

    @property
    def ws(self) -> WebSocketPort:
        """Return the bound `WebSocketPort`.

        Exposed for advanced domain code that needs to send custom
        WebSocket commands (e.g. ``timer/create``) which are neither
        services nor event subscriptions.
        """
        return self._ws

    @property
    def rest(self) -> RestPort:
        """Return the bound `RestPort`."""
        return self._rest

    async def call(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        *,
        prefer: ServicePolicy | None = None,
    ) -> Any:
        """Invoke a Home Assistant service.

        Parameters
        ----------
        domain : str
            The service domain.
        service : str
            The service name.
        data : dict or None, optional
            Service data payload.
        prefer : ServicePolicy or None, optional
            Per-call policy override. ``None`` uses the default policy.

        Returns
        -------
        Any
            The result returned by Home Assistant.

        Raises
        ------
        ConnectionClosedError
            If ``prefer="ws"`` is requested but the WebSocket is not connected.
        """
        policy: ServicePolicy = prefer if prefer is not None else self._default_policy
        if policy == "rest":
            return await self._rest.call_service(domain, service, data)
        if policy == "ws":
            if not self._ws.connected:
                raise ConnectionClosedError(
                    "Service call requested via WebSocket but WS is not connected"
                )
            return await self._call_ws(domain, service, data)
        # auto
        if self._ws.connected:
            return await self._call_ws(domain, service, data)
        return await self._rest.call_service(domain, service, data)

    async def _call_ws(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None,
    ) -> Any:
        """Send the WebSocket ``call_service`` payload."""
        payload: dict[str, Any] = {
            "type": "call_service",
            "domain": domain,
            "service": service,
        }
        if data:
            payload["service_data"] = data
        return await self._ws.send_command(payload)
