"""Base class shared by all agents."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

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

    def check(self, capability: str) -> bool:
        return cap_registry.check(self.name, capability)

    def require(self, capability: str) -> None:
        cap_registry.require(self.name, capability)

    async def chat(self, messages: list[dict], skill: str | None = None, **kwargs) -> str:
        chosen_skill = skill or (self._caps.preferred_skills[0] if self._caps.preferred_skills else "general")
        return await mpi_chat(
            skill=chosen_skill,
            agent=self.name,
            messages=messages,
            **kwargs,
        )

    @abstractmethod
    async def handle(self, payload: dict) -> dict:
        """Handle an incoming bus message. Return a response dict."""
