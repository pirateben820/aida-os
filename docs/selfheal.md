# Self-Heal Daemon

## Entry point
`python -m aidad.selfheal` — also runs as `aida-selfheal.service`

## What it watches (every 30 seconds)
- Systemd services: `aidad`, `ollama`, `docker`, `NetworkManager`
- Docker container: `nats`
- Available RAM — drops page cache if below 512 MB free
- Disk space — logs warning if `/` has less than 1 GB free

## What it does when something breaks
- Failed systemd service → `systemctl restart <service>`
- NATS container stopped → `docker restart nats`
- Low memory → `echo 1 > /proc/sys/vm/drop_caches`

## Action log
Every action is written to `~/.aida/selfheal.log` as JSON lines:
```json
{"ts": "2026-06-04T12:00:00", "action": "restart_service", "detail": "ollama.service"}
```
`aida-chat` reads the last 20 lines of this log and injects them into AIDA's context
so the user can ask "what did you fix?"

## Adding a new watch target
1. Add detection logic in `heal_loop()`
2. Add a repair action
3. Call `_log_action(action, detail)` — never skip logging

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `Permission denied` on drop_caches | Not running as root | Service must run as root |
| `systemctl not found` | Not on systemd system | Check runs on installed system, not dev machine |
