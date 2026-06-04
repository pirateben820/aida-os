# aidad — Core Daemon

## Entry point
`python -m aidad` → `aidad/__main__.py` → `AidaDaemon.run()`

## What it does
- Detects hardware (CPU/RAM/GPU) on startup
- Loads model registry from `config/models.yaml`
- Builds the scheduler (picks best model per skill + available VRAM/RAM)
- Initialises the P2P seeder (seeds installed models on startup)
- Starts the self-improve loop as an asyncio task
- Serves a FastAPI HTTP API on `127.0.0.1:8421`

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/hardware` | CPU/RAM/GPU inventory |
| GET | `/models` | All models in registry |
| POST | `/schedule` | Pick model for `{skill, agent}` |
| GET | `/seeder/stats` | Torrent seeding stats |
| POST | `/seeder/seed/{model_id}` | Start seeding a model |
| GET | `/seeder/magnets` | Known magnet links |

## Key files

| File | Purpose |
|---|---|
| `aidad/daemon.py` | Wires all components, starts uvicorn |
| `aidad/hardware.py` | psutil + nvidia-smi + rocm-smi detection |
| `aidad/registry.py` | Loads and queries `config/models.yaml` |
| `aidad/scheduler.py` | Selects model by skill + resource constraints |
| `aidad/settings.py` | Pydantic settings from `config/settings.yaml` |
| `aidad/api.py` | FastAPI app and route definitions |
| `aidad/selfheal.py` | Background service monitor (see selfheal.md) |
| `aidad/selfimprove.py` | Usage tracker and config tuner (see selfimprove.md) |
| `aidad/chat.py` | Terminal chat UI |

## Dependencies
`fastapi`, `uvicorn`, `psutil`, `pyyaml`, `pydantic`, `litellm`, `nats-py`

## Systemd service
`/etc/systemd/system/aidad.service` — starts after `docker.service` and `ollama.service`.
Runs as root (required for hardware access and service management).

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `models.yaml not found` | Wrong working directory | Run from project root |
| Port 8421 in use | Another aidad running | `systemctl stop aidad` |
| Seeder disabled | `libtorrent` not installed | `pacman -S python-libtorrent` |
