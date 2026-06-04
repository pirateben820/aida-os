"""Free-tier AI provider registry for the setup wizard.

Each provider listed here has a genuinely free API tier — no credit card
required (or a free daily/monthly allowance that covers one setup session).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FreeProvider:
    name: str           # display name
    key: str            # short key used in selection menu
    litellm_model: str  # model string LiteLLM understands
    env_var: str        # environment variable for the API key
    get_key_url: str    # where to get a free key
    free_note: str      # one-line description of the free tier


FREE_PROVIDERS: list[FreeProvider] = [
    FreeProvider(
        name="Google Gemini",
        key="gemini",
        litellm_model="gemini/gemini-1.5-flash",
        env_var="GEMINI_API_KEY",
        get_key_url="https://aistudio.google.com/app/apikey",
        free_note="Free tier: 15 requests/min, 1 500 requests/day — no card needed",
    ),
    FreeProvider(
        name="OpenRouter (free models)",
        key="openrouter",
        litellm_model="openrouter/meta-llama/llama-3.1-8b-instruct:free",
        env_var="OPENROUTER_API_KEY",
        get_key_url="https://openrouter.ai/keys",
        free_note="Free tier: several free models, rate-limited — no card needed",
    ),
    FreeProvider(
        name="Groq",
        key="groq",
        litellm_model="groq/llama3-8b-8192",
        env_var="GROQ_API_KEY",
        get_key_url="https://console.groq.com/keys",
        free_note="Free tier: 14 400 requests/day — no card needed",
    ),
    FreeProvider(
        name="Cohere",
        key="cohere",
        litellm_model="command-r",
        env_var="COHERE_API_KEY",
        get_key_url="https://dashboard.cohere.com/api-keys",
        free_note="Free trial key: 1 000 requests/month — no card needed",
    ),
    FreeProvider(
        name="Anthropic Claude (paid)",
        key="anthropic",
        litellm_model="claude-haiku-4-5-20251001",
        env_var="ANTHROPIC_API_KEY",
        get_key_url="https://console.anthropic.com/",
        free_note="Paid — but cheapest model (Haiku) costs ~$0.001 for one setup session",
    ),
    FreeProvider(
        name="OpenAI ChatGPT (paid)",
        key="openai",
        litellm_model="gpt-4o-mini",
        env_var="OPENAI_API_KEY",
        get_key_url="https://platform.openai.com/api-keys",
        free_note="Paid — gpt-4o-mini costs ~$0.001 for one setup session",
    ),
]


def get_provider(key: str) -> FreeProvider | None:
    return next((p for p in FREE_PROVIDERS if p.key == key), None)


def already_configured() -> FreeProvider | None:
    """Return the first provider whose API key is already in the environment."""
    import os
    for p in FREE_PROVIDERS:
        if os.environ.get(p.env_var):
            return p
    return None
