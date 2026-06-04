# Agents

## Base class
`agents/base.py` — `BaseAgent`
- Reads capability definition from `config/agents.yaml` on init
- `self.chat()` calls `mpi/client.py` → LiteLLM → scheduler → model
- `self.require(cap)` raises `PermissionError` if not allowed
- Every agent must implement `async handle(payload: dict) -> dict`

## Agents in alpha

| Agent | File | Active in alpha | Primary skill |
|---|---|---|---|
| AIDA | `agents/aida.py` | yes | general |
| Hermes | `agents/hermes.py` | yes | general |
| Archon | `agents/archon.py` | no | coding |
| SysAdmin | `agents/sysadmin.py` | no | reasoning |
| Security | `agents/security.py` | no | reasoning |
| Research | `agents/research.py` | no | general |
| Storage | `agents/storage.py` | no | general |

## Adding a new agent

1. Create `agents/<name>.py` subclassing `BaseAgent`, set `name = "<name>"`
2. Add entry to `config/agents.yaml` with `can` / `cannot` lists
3. Register it on the NATS bus in Phase 2

## Capability enforcement
Every capability check goes through `capabilities/model.py` → `CapabilityRegistry`.
Default is **deny** — if a capability is not in `can`, it is forbidden.
Never bypass `self.require()` with a try/except.

## Hermes memory
Uses ChromaDB stored at `~/.aida/hermes/memory/`.
`remember(text, id)` — stores a document.
`recall(query, n)` — semantic search, returns top-n strings.
Requires `nomic-embed-text` model to be pulled for embeddings.

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `No capability definition found` | Agent name not in agents.yaml | Add entry to config/agents.yaml |
| `PermissionError` on capability | Action not in `can` list | Add to agents.yaml or don't do it |
| ChromaDB import error | Package not installed | `pip install chromadb` |
