# aida-chat — Terminal Interface

## Entry point
`python -m aidad.chat` or `aida-chat` (after pip install)

## SSH shortcut
The `aida` system user has `ForceCommand /opt/aida-os/.venv/bin/aida-chat` in sshd config.
`ssh aida@<vm-ip>` drops directly into chat. Password: `aida` (should be changed).

## What AIDA knows in every message
Context injected automatically before each reply:
- Live CPU/RAM/disk usage (via psutil)
- Last 20 lines of `~/.aida/selfheal.log`
- Last 20 lines of `~/.aida/improvements.log`

## Alpha scope enforcement
The system prompt explicitly tells AIDA:
- Only answer questions about the system
- Do not pretend to do coding, web search, or file management
- Be honest about what alpha can and cannot do

## Conversation history
Last 10 exchanges kept in memory (20 messages). Older context is dropped.
No persistence between sessions in alpha.

## IP hint
On startup, detects and prints `ssh aida@<local-ip>` so the user knows how to connect remotely.

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` on MPI | aidad not running | `systemctl start aidad` |
| `No model available` | No models pulled | `ollama pull deepseek-r1:1.5b` |
| Blank responses | Model returned empty | Try again or check Ollama logs |
