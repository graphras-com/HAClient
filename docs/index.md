# HaClient

Async-first, high-level Python client for Home Assistant with REST and WebSocket support.

## Features

- Async context manager with automatic WebSocket connection and state priming
- Typed domain accessors: light, switch, climate, cover, sensor, binary sensor, media player
- Real-time state change listeners with granular filtering
- Synchronous blocking wrapper for scripts, REPL, and Jupyter
- Automatic WebSocket reconnection with exponential backoff
- Fully typed (PEP 561) with strict mypy enforcement

## Installation

```bash
pip install haclient
```

Or install from source:

```bash
git clone https://github.com/graphras-com/HaClient.git
cd HaClient
pip install .
```

## Quick Start

### Async

```python
from haclient import HAClient

async with HAClient("http://localhost:8123", token="YOUR_TOKEN") as ha:
    light = ha.light("kitchen")
    await light.turn_on(brightness=200)
```

### Synchronous

```python
from haclient import SyncHAClient

with SyncHAClient("http://localhost:8123", token="YOUR_TOKEN") as ha:
    light = ha.light("kitchen")
    light.turn_on(brightness=200)
```
