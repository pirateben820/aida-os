# MPI — Model Provider Interface

## What it is
A thin wrapper around LiteLLM. Every agent calls `mpi_chat()` instead of
any provider SDK directly. This keeps provider logic in one place.

## How it works
1. Agent calls `mpi_chat(skill="coding", agent="archon", messages=[...])`
2. MPI asks aidad `/schedule` for the best model for that skill
3. aidad scheduler returns a `litellm_model_id` (e.g. `ollama/qwen2.5-coder:7b`)
4. MPI calls `litellm.acompletion(model=..., messages=...)`
5. Returns the response string

## LiteLLM model ID format

| Provider | Format | Example |
|---|---|---|
| Ollama | `ollama/<model>` | `ollama/qwen2.5-coder:7b` |
| OpenAI | `<model>` | `gpt-4o-mini` |
| Anthropic | `<model>` | `claude-haiku-4-5-20251001` |
| vLLM | `openai/<model>` | `openai/qwen2.5-coder:7b` |
| Groq | `groq/<model>` | `groq/llama3-8b-8192` |
| OpenRouter | `openrouter/<model>` | `openrouter/mistralai/mistral-7b-instruct:free` |
| Gemini | `gemini/<model>` | `gemini/gemini-1.5-flash` |

## Environment variables LiteLLM reads

```
ANTHROPIC_API_KEY
OPENAI_API_KEY
OPENROUTER_API_KEY
GROQ_API_KEY
GEMINI_API_KEY
COHERE_API_KEY
OLLAMA_API_BASE   (default: http://127.0.0.1:11434)
```

## Streaming
Pass `stream=True` to `mpi_chat()` — returns an `AsyncIterator[str]` of chunks.

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` on Ollama | Ollama not running | `systemctl start ollama` |
| `model not found` | Model not pulled | `ollama pull <model>` |
| `API key missing` | Cloud model, no key set | Set env var or use local model |
| Scheduler returns `no model available` | VRAM too low | Pull a smaller model |
