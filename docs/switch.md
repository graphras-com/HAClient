# Switch

`haclient.domains.switch.Switch` — domain: `"switch"`

Inherits from [`Entity`](base.md#hacliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `is_on` | `bool` | Switch is on |

## Methods

| Method | Signature |
|---|---|
| `turn_on` | `async ()` |
| `turn_off` | `async ()` |
| `toggle` | `async ()` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_turn_on` | State transitions to `"on"` |
| `@on_turn_off` | State transitions to `"off"` |
