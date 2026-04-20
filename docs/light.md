# Light

`ha_client.domains.light.Light` — domain: `"light"`

Inherits from [`Entity`](base.md#ha_cliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `is_on` | `bool` | Light is on |
| `brightness` | `int \| None` | Brightness (0–255) |
| `rgb_color` | `tuple[int, int, int] \| None` | RGB color |

## Methods

| Method | Signature |
|---|---|
| `turn_on` | `async (*, brightness=None, rgb_color=None, color_temp=None, transition=None, **extra)` |
| `turn_off` | `async (*, transition=None)` |
| `toggle` | `async ()` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_turn_on` | State transitions to `"on"` |
| `@on_turn_off` | State transitions to `"off"` |
| `@on_brightness_change` | `brightness` attribute changes |
| `@on_color_change` | `rgb_color` attribute changes |
