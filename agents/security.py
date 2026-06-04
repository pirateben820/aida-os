"""Security agent — firewall, intrusion detection, auditing."""
from __future__ import annotations

from agents.base import BaseAgent

SYSTEM_PROMPT = """You are the Security agent for AIDA OS.
You monitor firewalls, authentication logs, and system integrity.
You can raise security alerts and modify firewall rules.
You NEVER read secret values, only metadata.
You have no external network access.
"""


class SecurityAgent(BaseAgent):
    name = "security"

    async def handle(self, payload: dict) -> dict:
        task = payload.get("task", "")
        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            require_local=True,  # Security agent always runs local
        )
        return {"agent": self.name, "response": response}
