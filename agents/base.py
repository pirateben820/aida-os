"""Base class shared by all agents."""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from bus.client import subscribe_reply
from capabilities.model import registry as cap_registry
from mpi.client import mpi_chat


class BaseAgent(ABC):
    name: str  # must be set on subclass, matches agents.yaml key

    def __init__(self) -> None:
        self.log = logging.getLogger(f"agent.{self.name}")
        defn = cap_registry.get(self.name)
        if defn is None:
            raise ValueError(f"No capability definition found for agent '{self.name}'")
        self._caps = defn
        self.log.info("Agent '%s' initialised", self.name)

    # ── capabilities ──────────────────────────────────────────────────────────

    def check(self, capability: str) -> bool:
        return cap_registry.check(self.name, capability)

    def require(self, capability: str) -> None:
        cap_registry.require(self.name, capability)

    # ── model access ──────────────────────────────────────────────────────────

    async def chat(self, messages: list[dict], skill: str | None = None, **kwargs) -> str:
        chosen_skill = skill or (
            self._caps.preferred_skills[0] if self._caps.preferred_skills else "general"
        )
        return await mpi_chat(
            skill=chosen_skill,
            agent=self.name,
            messages=messages,
            **kwargs,
        )

    # ── bus ───────────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Subscribe to the bus and process messages until cancelled.

        Subject: aida.agent.<name>.request
        All incoming messages are passed to handle() and the result is replied.
        """
        subject = f"aida.agent.{self.name}.request"
        await subscribe_reply(subject, self.handle)
        self.log.info("Agent '%s' listening on %s", self.name, subject)
        # Keep the coroutine alive — NATS callbacks run on the event loop
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            self.log.info("Agent '%s' stopped", self.name)

    # ── handler (subclasses implement this) ───────────────────────────────────

    @abstractmethod
    async def handle(self, payload: dict) -> dict:
        """Handle an incoming bus message. Return a response dict."""
