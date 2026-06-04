# Self-Improve Daemon

## Entry point
Runs as an asyncio task inside `aidad` (not a separate process).
Also callable standalone: `python -m aidad.selfimprove`

## What it tracks
Every time the scheduler picks a model, it calls `record_usage()` which appends
a JSON line to `~/.aida/usage.jsonl`:
```json
{"ts": "...", "event": "model_used", "model": "qwen2.5-coder:7b", "skill": "coding"}
{"ts": "...", "event": "agent_invoked", "agent": "archon"}
```

## What it does (every 5 minutes, after 10+ events)
1. **Reorders models** — most-used models move to top of `config/models.yaml`
   so the scheduler picks them first (faster, no VRAM recalculation needed)
2. **Suggests disabling unused agents** — logged to `~/.aida/improvements.log`
3. **Warns about memory pressure** — if RAM >85%, logs suggestion to use smaller model

## Improvement log
`~/.aida/improvements.log` — plain text, one line per suggestion.
`aida-chat` injects the last 20 lines into AIDA's context.

## Rules
- Never delete or modify user data
- Never apply destructive changes automatically
- Always log before changing anything
- Config changes (`models.yaml` reorder) are safe — fully reversible

## Adding a new improvement
1. Add analysis function that reads `_load_usage()`
2. Call `_log_improvement(action, detail)` before any change
3. Keep it non-destructive
