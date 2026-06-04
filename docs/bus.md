# Bus — NATS Message Bus

## What it is
Inter-agent communication layer using NATS (nats.io).
Agents publish and subscribe to subjects. Replies use NATS request/reply.

## Subject naming convention
```
aida.agent.<agent_name>.<action>
```
Examples:
```
aida.agent.archon.task_request
aida.agent.hermes.memory_query
aida.agent.sysadmin.service_restart
```

## API (`bus/client.py`)
```python
await publish(subject, payload_dict)
await subscribe(subject, async_handler)
result = await request(subject, payload_dict, timeout=10.0)
```

## Running NATS (development)
```bash
docker compose -f docker-compose.dev.yml up -d
# or
docker run -d --name nats -p 4222:4222 nats:latest
```

## NATS in production (installed system)
The `nats` Docker container is started by aidad and watched by selfheal.
If it crashes, selfheal restarts it automatically.

## Phase 2 note
In Phase 2, each agent will call `bus.subscribe()` in a `run()` loop.
Currently agents only have `handle()` — bus wiring is not yet done.

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` | NATS not running | `docker start nats` |
| `nats-py` not installed | Missing dep | `pip install nats-py` |
| Timeout on `request()` | Agent not subscribed | Check agent's `run()` loop is active |
