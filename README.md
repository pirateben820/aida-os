# AIDA OS

AI-native operating environment built on Arch Linux.

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| Model routing (MPI) | LiteLLM |
| Local inference | Ollama → vLLM (scale) |
| Message bus | NATS |
| Core daemon | aidad (Python/asyncio) |
| Hardware detection | lshw, nvidia-smi, rocm-smi |
| Base OS | Arch Linux |

## Structure

```
aida-os/
├── aidad/          # Core daemon — hardware, registry, scheduler
├── agents/         # Agent definitions (AIDA, Hermes, Archon, …)
├── mpi/            # Model Provider Interface (LiteLLM wrapper)
├── bus/            # NATS client helpers
├── capabilities/   # Permission/capability system
├── config/         # Model registry YAML, agent caps YAML
└── scripts/        # Install and bootstrap scripts
```

## Phase Roadmap

- [x] Phase 1 — aidad daemon, model registry, scheduler skeleton
- [ ] Phase 2 — Agent framework, capability system, message bus
- [ ] Phase 3 — AI Task Manager, desktop integration
- [ ] Phase 4 — Cluster / multi-node scheduling
- [ ] Phase 5 — Installer, branding, distribution packaging

## Quick Start (development)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a starter model
ollama pull qwen2.5-coder:7b

# 3. Install Python deps
pip install -e ".[dev]"

# 4. Start NATS (Docker)
docker run -d --name nats -p 4222:4222 nats:latest

# 5. Start aidad
python -m aidad
```
