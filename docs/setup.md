# Setup — First-Boot Wizard

## Flow
1. `aida-firstboot.sh` runs on first login (via `/etc/profile.d/`)
2. Calls `aida-setup` → `setup/wizard.py`
3. Scans hardware
4. User picks a free cloud AI provider (or one is auto-detected from env)
5. 7 questions asked in plain English
6. Cloud AI returns a JSON `UserProfile`
7. User confirms the plan
8. `setup/installer.py` installs desktop, pulls models, writes config
9. Firstboot script deletes itself
10. Drops into `aida-chat`

## Free providers (no credit card)

| Key | Provider | Model | Daily limit |
|---|---|---|---|
| `gemini` | Google Gemini | gemini-1.5-flash | 1500 req/day |
| `openrouter` | OpenRouter | llama-3.1-8b-instruct:free | rate limited |
| `groq` | Groq | llama3-8b-8192 | 14400 req/day |
| `cohere` | Cohere | command-r | 1000/month |

Auto-detected from env: checks `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`,
`COHERE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` in that order.

## UserProfile
Saved to `~/.aida/profile.yaml`. Contains:
- `use_cases` — what the user does
- `skill_level` — beginner/intermediate/expert
- `privacy_level` — standard/high/paranoid
- `air_gapped` — never use cloud AI if true
- `desktop` — environment, terminal, theme, layout
- `models.to_pull` — Ollama models to download
- `agents.enabled` — which agents to activate

## Recommender fallback
If no cloud key provided, `setup/recommender.py` uses keyword matching on
the conversation text to pick models and agents. Less accurate but always works.

## Model pull order
1. Try torrent (check `config/model_torrents.yaml` for magnet link)
2. Fall back to `ollama pull <model>` direct download

## Common failures

| Error | Cause | Fix |
|---|---|---|
| Wizard exits immediately | Profile already exists | Delete `~/.aida/profile.yaml` to re-run |
| Cloud AI returns invalid JSON | Model gave prose instead of JSON | Retry — or use a different provider |
| `ollama pull` hangs | No network | Check network, then retry |
| Desktop packages fail | pacman not available | Only installs on Arch Linux |
