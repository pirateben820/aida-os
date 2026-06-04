# AIDA OS — Developer Reference for AI

Read this before touching any component. Each section has a docs link for detail.

## Project goal
AI-native Linux distro built on Arch Linux. Alpha runs in VMs only.
AI watches, heals, and improves the system. No general assistant in alpha.

## Directory map

| Path | What it is | Docs |
|---|---|---|
| `aidad/` | Core daemon — hardware, registry, scheduler, API | [docs/aidad.md](docs/aidad.md) |
| `aidad/selfheal.py` | Restarts failed services, frees memory | [docs/selfheal.md](docs/selfheal.md) |
| `aidad/selfimprove.py` | Learns usage patterns, reorders models | [docs/selfimprove.md](docs/selfimprove.md) |
| `aidad/chat.py` | Terminal chat interface (`aida-chat`) | [docs/chat.md](docs/chat.md) |
| `agents/` | Agent definitions (AIDA, Hermes, Archon, …) | [docs/agents.md](docs/agents.md) |
| `mpi/` | Model Provider Interface — LiteLLM wrapper | [docs/mpi.md](docs/mpi.md) |
| `bus/` | NATS pub/sub helpers | [docs/bus.md](docs/bus.md) |
| `capabilities/` | Permission system — default deny | [docs/capabilities.md](docs/capabilities.md) |
| `seeder/` | libtorrent P2P model distribution | [docs/seeder.md](docs/seeder.md) |
| `setup/` | First-boot wizard + installer | [docs/setup.md](docs/setup.md) |
| `archiso/` | ISO build profile | [docs/archiso.md](docs/archiso.md) |
| `config/` | models.yaml, agents.yaml, settings.yaml | [docs/config.md](docs/config.md) |
| `.github/workflows/` | GitHub Actions ISO build | [docs/ci.md](docs/ci.md) |

## Stack

| Layer | Tool | Why |
|---|---|---|
| Agent orchestration | LangGraph | Purpose-built multi-agent graphs |
| Model routing | LiteLLM | One API for Ollama/vLLM/OpenAI/Anthropic/etc |
| Local inference | Ollama (primary), vLLM (scale) | Zero-config local models |
| Message bus | NATS | Lightweight, request/reply built in |
| Memory (Hermes) | ChromaDB | Embedded, local-only |
| Terminal UI | rich | Already a dep, no extra install |
| Hardware detection | psutil + nvidia-smi + rocm-smi | Already on every Linux system |

## Rules

- **Disk budget: 20 GB total.** Starter models ~6 GB. Never add models that push total over 12 GB without checking.
- **Alpha scope only:** self-heal, self-improve, system explain. No coding agent, no web search, no file management.
- **VM only in alpha.** Never remove the VM detection check in `aida-install`.
- **Default deny capabilities.** Every new agent action must be explicitly added to `config/agents.yaml`.
- **Local first.** Scheduler always prefers local models. Cloud only when `local_first=false` or resource unavailable.
- **Read the relevant docs file before modifying a component.**
