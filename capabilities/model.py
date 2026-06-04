"""Capability model and enforcement."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

_AGENTS_PATH = Path(__file__).parent.parent / "config" / "agents.yaml"


class AgentCapabilities(BaseModel):
    can: list[str] = Field(default_factory=list)
    cannot: list[str] = Field(default_factory=list)


class AgentDefinition(BaseModel):
    description: str = ""
    preferred_skills: list[str] = Field(default_factory=list)
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)


class CapabilityRegistry:
    def __init__(self, path: Path = _AGENTS_PATH) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        self._load(path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            log.warning("agents.yaml not found at %s", path)
            return
        raw = yaml.safe_load(path.read_text())
        for name, data in raw.get("agents", {}).items():
            self._agents[name] = AgentDefinition.model_validate(data)
        log.info("Loaded capabilities for %d agent(s)", len(self._agents))

    def get(self, agent: str) -> AgentDefinition | None:
        return self._agents.get(agent)

    def check(self, agent: str, capability: str) -> bool:
        """Return True if the agent is allowed to perform capability."""
        defn = self._agents.get(agent)
        if defn is None:
            log.warning("Unknown agent '%s' — capability check denied", agent)
            return False
        if capability in defn.capabilities.cannot:
            return False
        if capability in defn.capabilities.can:
            return True
        # Default deny — if it's not explicitly allowed, it's forbidden.
        return False

    def require(self, agent: str, capability: str) -> None:
        """Raise PermissionError if the agent cannot perform capability."""
        if not self.check(agent, capability):
            raise PermissionError(
                f"Agent '{agent}' does not have capability '{capability}'"
            )


# Module-level singleton — agents import this directly
registry = CapabilityRegistry()
