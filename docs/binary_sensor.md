# Binary Sensor

`haclient.domains.binary_sensor.BinarySensor` — domain: `"binary_sensor"`

Inherits from [`Entity`](base.md#hacliententityentity). Read-only.

## Properties

| Name | Type | Description |
|---|---|---|
| `is_on` | `bool` | Sensor is on |
| `device_class` | `str \| None` | Device class (e.g. `"motion"`, `"door"`) |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_turn_on` | State transitions to `"on"` |
| `@on_turn_off` | State transitions to `"off"` |
