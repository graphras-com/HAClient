# Climate

`haclient.domains.climate.Climate` — domain: `"climate"`

Inherits from [`Entity`](base.md#hacliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `current_temperature` | `float \| None` | Measured temperature |
| `target_temperature` | `float \| None` | Target setpoint |
| `hvac_mode` | `str` | Active HVAC mode (equals `state`) |
| `hvac_modes` | `list[str]` | Supported modes |

## Methods

| Method | Signature |
|---|---|
| `set_temperature` | `async (temperature: float, *, hvac_mode=None, **extra)` |
| `set_hvac_mode` | `async (hvac_mode: str)` |
| `set_fan_mode` | `async (fan_mode: str)` |
| `turn_on` | `async ()` |
| `turn_off` | `async ()` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_hvac_mode_change` | State string (HVAC mode) changes |
| `@on_temperature_change` | `current_temperature` attribute changes |
| `@on_target_temperature_change` | `temperature` attribute changes |
