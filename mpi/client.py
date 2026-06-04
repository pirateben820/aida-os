"""MPI client — agents call this instead of any provider SDK directly.

Usage:
    from mpi.client import mpi_chat

    response = await mpi_chat(
        skill="coding",
        agent="archon",
        messages=[{"role": "user", "content": "Write a hello-world in Go."}],
    )
"""
from __future__ import annotations

import logging
import os
from typing import AsyncIterator

import httpx
import litellm
from litellm import acompletion

log = logging.getLogger(__name__)

# Silence LiteLLM's noisy default logging
litellm.suppress_debug_info = True

_AIDAD_URL = os.environ.get("AIDAD_URL", "http://127.0.0.1:8421")


async def _resolve_model(skill: str, agent: str, require_local: bool = False) -> str:
    """Ask aidad scheduler which model to use."""
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(
            f"{_AIDAD_URL}/schedule",
            json={"skill": skill, "agent": agent, "require_local": require_local},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Scheduler: {data['error']}")
        return data["litellm_model_id"]


async def mpi_chat(
    skill: str,
    agent: str,
    messages: list[dict],
    stream: bool = False,
    require_local: bool = False,
    **kwargs,
) -> str | AsyncIterator[str]:
    """Route a chat request through the MPI.

    Returns the assistant message string (or an async iterator when stream=True).
    """
    model = await _resolve_model(skill, agent, require_local)
    log.debug("mpi_chat agent=%s skill=%s model=%s", agent, skill, model)

    response = await acompletion(model=model, messages=messages, stream=stream, **kwargs)

    if stream:

        async def _stream() -> AsyncIterator[str]:
            async for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                yield delta

        return _stream()

    return response.choices[0].message.content
