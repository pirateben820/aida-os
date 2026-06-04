"""LangGraph orchestrator for AIDA OS alpha.

Alpha graph:
    START → get_memories → aida_respond → END

AIDA always asks Hermes for relevant memories first, then generates
a response with full system context + memories injected.
"""
from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from bus.client import request as bus_request

log = logging.getLogger(__name__)

_HERMES_SUBJECT = "aida.agent.hermes.request"

_ALPHA_SYSTEM_PROMPT = """You are AIDA, the AI built into AIDA OS.

Alpha scope — you only help with:
1. Explaining what is happening on this system
2. What you have fixed or improved
3. System health, models, services
4. Suggestions to improve the setup

Do NOT pretend to do coding, web search, or file management — not in alpha.
Be honest, direct, and concise.
"""


class AlphaState(TypedDict):
    user_message: str
    system_context: str
    memories: list[str]
    response: str


async def _get_memories(state: AlphaState) -> AlphaState:
    """Ask Hermes for memories relevant to the user message."""
    try:
        result = await bus_request(
            _HERMES_SUBJECT,
            {"action": "recall", "query": state["user_message"], "n": 5},
            timeout=5.0,
        )
        memories = result.get("memories", [])
    except Exception as exc:
        log.debug("Hermes unavailable, skipping memories: %s", exc)
        memories = []
    return {**state, "memories": memories}


async def _aida_respond(state: AlphaState) -> AlphaState:
    """Generate AIDA's response using system context + memories."""
    from mpi.client import mpi_chat

    memory_block = (
        "Relevant memories from Hermes:\n" + "\n".join(f"- {m}" for m in state["memories"])
        if state["memories"]
        else ""
    )

    messages = [
        {"role": "system", "content": _ALPHA_SYSTEM_PROMPT},
        {"role": "system", "content": state["system_context"]},
    ]
    if memory_block:
        messages.append({"role": "system", "content": memory_block})
    messages.append({"role": "user", "content": state["user_message"]})

    response = await mpi_chat(skill="general", agent="aida", messages=messages)
    return {**state, "response": response}


def build_graph():
    g = StateGraph(AlphaState)
    g.add_node("get_memories", _get_memories)
    g.add_node("aida_respond", _aida_respond)
    g.add_edge(START, "get_memories")
    g.add_edge("get_memories", "aida_respond")
    g.add_edge("aida_respond", END)
    return g.compile()


# Module-level compiled graph — import and call ainvoke()
graph = build_graph()
