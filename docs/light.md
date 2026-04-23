# Light

`haclient.domains.light.Light` — domain: `"light"`

Inherits from [`Entity`](base.md#hacliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `is_on` | `bool` | Light is on |
| `brightness` | `int \| None` | Brightness (0–255) |
| `rgb_color` | `tuple[int, int, int] \| None` | RGB color |
| `kelvin` | `int \| None` | Current color temperature in Kelvin |
| `min_kelvin` | `int \| None` | Minimum supported color temperature in Kelvin |
| `max_kelvin` | `int \| None` | Maximum supported color temperature in Kelvin |

## Methods

| Method | Signature |
|---|---|
| `turn_on` | `async (*, brightness=None, rgb_color=None, color_temp=None, kelvin=None, transition=None, **extra)` |
| `turn_off` | `async (*, transition=None)` |
| `toggle` | `async ()` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_turn_on` | State transitions to `"on"` |
| `@on_turn_off` | State transitions to `"off"` |
| `@on_brightness_change` | `brightness` attribute changes |
| `@on_color_change` | `rgb_color` attribute changes |
| `@on_kelvin_change` | `color_temp_kelvin` attribute changes |
