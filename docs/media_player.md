# Media Player

`ha_client.domains.media_player.MediaPlayer` — domain: `"media_player"`

Inherits from [`Entity`](base.md#ha_cliententityentity).

## Properties

| Name | Type | Description |
|---|---|---|
| `is_playing` | `bool` | Currently playing |
| `is_paused` | `bool` | Currently paused |
| `volume_level` | `float \| None` | Volume (0.0–1.0) |
| `source` | `str \| None` | Current input source |

## Methods

| Method | Signature |
|---|---|
| `play` | `async ()` |
| `pause` | `async ()` |
| `play_pause` | `async ()` |
| `stop` | `async ()` |
| `next` | `async ()` |
| `previous` | `async ()` |
| `set_volume` | `async (level: float)` |
| `mute` | `async (muted: bool = True)` |
| `turn_on` | `async ()` |
| `turn_off` | `async ()` |
| `select_source` | `async (source: str)` |
| `play_media` | `async (media_content_type: str, media_content_id: str, **extra)` |
| `browse_media` | `async (media_content_type: str, media_content_id: str) -> dict` |
| `favorites` | `async (*, max_depth=6, max_nodes=2000) -> list[FavoriteItem]` |

## Event Decorators

| Decorator | Fires when |
|---|---|
| `@on_volume_change` | `volume_level` attribute changes |
| `@on_mute_change` | `is_volume_muted` attribute changes |
| `@on_source_change` | `source` attribute changes |
| `@on_play` | State transitions to `"playing"` |
| `@on_pause` | State transitions to `"paused"` |
| `@on_stop` | State transitions to `"idle"` |

---

## `FavoriteItem`

Returned by `MediaPlayer.favorites()`.

| Attribute | Type | Description |
|---|---|---|
| `title` | `str` | Display name |
| `media_content_id` | `str` | HA content ID |
| `media_content_type` | `str` | HA content type |
| `thumbnail` | `str \| None` | Image URL |
| `category` | `str \| None` | Parent folder title |
| `media_class` | `str \| None` | Raw HA media class |

### Methods

| Method | Signature |
|---|---|
| `play` | `async () -> None` |
