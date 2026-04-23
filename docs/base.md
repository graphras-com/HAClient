# Base Library

## `haclient.client.HAClient`

High-level orchestrator combining REST and WebSocket clients.

### Constructor

```python
HAClient(
    base_url: str,
    token: str,
    *,
    ws_url: str | None = None,
    session: aiohttp.ClientSession | None = None,
    reconnect: bool = True,
    ping_interval: float = 30.0,
    request_timeout: float = 30.0,
    verify_ssl: bool = True,
)
```

### Attributes

| Name | Type | Description |
|---|---|---|
| `registry` | `EntityRegistry` | Shared entity registry |
| `rest` | `RestClient` | REST sub-client |
| `ws` | `WebSocketClient` | WebSocket sub-client |
| `loop` | `AbstractEventLoop \| None` | Current event loop |

### Methods

| Method | Signature | Returns |
|---|---|---|
| `connect` | `async () -> None` | Connect WS, seed states, subscribe to `state_changed` |
| `close` | `async () -> None` | Close WS and REST clients |
| `call_service` | `async (domain, service, data, *, use_websocket=True)` | Service response |
| `refresh_all` | `async () -> None` | Refresh all registered entities via REST |

### Domain Accessors

Each returns (or creates) a domain entity instance.

| Method | Returns |
|---|---|
| `light(name)` | `Light` |
| `switch(name)` | `Switch` |
| `media_player(name)` | `MediaPlayer` |
| `climate(name)` | `Climate` |
| `cover(name)` | `Cover` |
| `sensor(name)` | `Sensor` |
| `binary_sensor(name)` | `BinarySensor` |

### Context Manager

```python
async with HAClient(url, token) as client:
    ...
```

---

## `haclient.sync.SyncHAClient`

Blocking wrapper around `HAClient`. Runs a dedicated event loop in a background thread.

### Constructor

Same parameters as `HAClient`.

### Methods

| Method | Signature | Description |
|---|---|---|
| `connect` | `() -> None` | Blocking connect |
| `close` | `() -> None` | Blocking close, stops loop thread |
| `call_service` | `(domain, service, data)` | Blocking service call |
| `refresh_all` | `() -> None` | Blocking refresh |

Domain accessors (`light`, `switch`, etc.) return `_SyncProxy` objects that automatically convert async calls to blocking.

### Context Manager

```python
with SyncHAClient(url, token) as client:
    ...
```

---

## `haclient.rest.RestClient`

HTTP REST API client.

### Constructor

```python
RestClient(
    base_url: str,
    token: str,
    *,
    session: aiohttp.ClientSession | None = None,
    timeout: float = 30.0,
    verify_ssl: bool = True,
)
```

### Methods

| Method | Signature | Returns |
|---|---|---|
| `close` | `async () -> None` | Close HTTP session |
| `ping` | `async () -> bool` | `GET /api/` connectivity check |
| `get_states` | `async () -> list[dict]` | All entity states |
| `get_state` | `async (entity_id: str) -> dict \| None` | Single entity state |
| `call_service` | `async (domain: str, service: str, data: dict \| None) -> list[dict]` | Call a service |

---

## `haclient.websocket.WebSocketClient`

WebSocket API client with auto-reconnect.

### Constructor

```python
WebSocketClient(
    url: str,
    token: str,
    *,
    session: aiohttp.ClientSession | None = None,
    reconnect: bool = True,
    ping_interval: float = 30.0,
    request_timeout: float = 30.0,
    verify_ssl: bool = True,
)
```

### Methods

| Method | Signature | Returns |
|---|---|---|
| `connect` | `async () -> None` | Connect and authenticate |
| `close` | `async () -> None` | Close socket, cancel tasks |
| `send_command` | `async (payload: dict, *, timeout: float \| None) -> Any` | Send command, await result |
| `subscribe_events` | `async (handler: EventHandler, event_type: str \| None) -> int` | Subscribe; returns subscription ID |
| `unsubscribe` | `async (subscription_id: int) -> None` | Unsubscribe |
| `ping` | `async (*, timeout: float \| None) -> None` | Send ping, await pong |
| `on_disconnect` | `(handler: Callable) -> Callable` | Register disconnect callback |

### Properties

| Name | Type | Description |
|---|---|---|
| `connected` | `bool` | Whether socket is open |

### Type Aliases

```python
EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]
```

---

## `haclient.entity.Entity`

Base class for all domain entities.

### Constructor

```python
Entity(entity_id: str, client: HAClient)
```

### Attributes

| Name | Type | Description |
|---|---|---|
| `domain` | `str` | Domain string (overridden by subclasses) |
| `entity_id` | `str` | Fully-qualified entity ID |
| `state` | `str` | Current state string (default `"unknown"`) |
| `attributes` | `dict[str, Any]` | Current attribute dict |

### Properties

| Name | Type | Description |
|---|---|---|
| `available` | `bool` | `True` if state not in `{"unavailable", "unknown"}` |

### Methods

| Method | Signature | Returns |
|---|---|---|
| `async_refresh` | `async () -> None` | Fetch latest state from REST |
| `call_service` | `async (service: str, data: dict \| None, *, domain: str \| None) -> Any` | Call service targeting this entity |
| `on_state_change` | `(func) -> func` | Decorator: register raw state change listener `(old_state, new_state)` |
| `remove_listener` | `(func) -> None` | Remove raw state change listener |
| `remove_granular_listener` | `(func) -> None` | Remove attribute/state-transition/state-value listener |

### Protected Methods (for subclasses)

| Method | Signature | Description |
|---|---|---|
| `_register_attr_listener` | `(attr_key: str, func) -> func` | Fire `(old_val, new_val)` on attribute change |
| `_register_state_transition_listener` | `(to_state: str, func) -> func` | Fire on transition to specific state |
| `_register_state_value_listener` | `(func) -> func` | Fire on any state string change |

### Type Aliases

```python
StateChangeHandler = Callable[[dict | None, dict | None], Any]
ValueChangeHandler = Callable[[Any, Any], Any]
```

---

## `haclient.registry.EntityRegistry`

Entity store with lookup and domain filtering.

### Methods

| Method | Signature | Returns |
|---|---|---|
| `register` | `(entity: Entity) -> None` | Store entity by ID |
| `unregister` | `(entity_id: str) -> None` | Remove entity |
| `get` | `(entity_id: str) -> Entity \| None` | Lookup by ID |
| `require` | `(entity_id: str) -> Entity` | Lookup or raise `EntityNotFoundError` |
| `resolve` | `(domain: str, name: str) -> str` | Resolve short name to full entity_id |
| `in_domain` | `(domain: str) -> list[Entity]` | All entities in a domain |
| `clear` | `() -> None` | Remove all entities |

Supports `__contains__`, `__iter__`, `__len__`.

---

## `haclient.exceptions`

| Exception | Base | Description |
|---|---|---|
| `HAClientError` | `Exception` | Base exception |
| `AuthenticationError` | `HAClientError` | Authentication failure |
| `ConnectionClosedError` | `HAClientError` | Unexpected WebSocket close |
| `CommandError` | `HAClientError` | HA returned error. Attrs: `code: str`, `message: str` |
| `TimeoutError` | `HAClientError` | Request timeout |
| `EntityNotFoundError` | `HAClientError` | Entity not found |
| `UnsupportedOperationError` | `HAClientError` | Unsupported operation |
