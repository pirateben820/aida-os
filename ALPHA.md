# AIDA OS — Alpha Scope

## What alpha does

- Installs as a VM guest (VirtualBox, QEMU/KVM, VMware)
- Runs a first-boot AI setup wizard (cloud AI, free tier)
- Pulls local AI models via torrent or Ollama
- AI watches the system and fixes problems automatically
- AI learns what the user needs and improves the configuration over time

## What alpha does NOT do

- No general chatbot / assistant features
- No coding agent (Archon) — not in alpha
- No research agent — not in alpha
- No cluster / multi-node — not in alpha
- No bare-metal install — VM only in alpha

## VM requirements

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 40 GB |
| GPU pass-through | not required | optional |
| Network | required for setup | can go offline after |

## Tested hypervisors

- VirtualBox 7+
- QEMU/KVM (virt-manager)
- VMware Workstation / Fusion

## Alpha AI responsibilities

1. **Self-heal** — detect broken services, failed mounts, crashed processes → fix them
2. **Self-improve** — watch what the user actually uses → tune model selection,
   agent config, and resource allocation over time
3. **System explain** — answer questions about what the system is doing and why
