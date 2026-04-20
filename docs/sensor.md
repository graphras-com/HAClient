# Sensor

`ha_client.domains.sensor.Sensor` — domain: `"sensor"`

Inherits from [`Entity`](base.md#ha_cliententityentity). Read-only.

## Properties

| Name | Type | Description |
|---|---|---|
| `unit_of_measurement` | `str \| None` | Unit string |
| `device_class` | `str \| None` | Device class (e.g. `"temperature"`) |
| `value` | `float \| str \| None` | State coerced to float if numeric |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_value_change` | State string changes |
