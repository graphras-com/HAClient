# Cover

`haclient.domains.cover.Cover` — domain: `"cover"`

Inherits from [`Entity`](base.md#hacliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `is_open` | `bool` | Cover is open |
| `is_closed` | `bool` | Cover is closed |
| `current_position` | `int \| None` | Position (0–100) |

## Methods

| Method | Signature |
|---|---|
| `open` | `async ()` |
| `close` | `async ()` |
| `stop` | `async ()` |
| `set_position` | `async (position: int)` |
| `toggle` | `async ()` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_open` | State transitions to `"open"` |
| `@on_close` | State transitions to `"closed"` |
| `@on_position_change` | `current_cover_position` attribute changes |
