"""SysAdmin agent — services, Docker, VMs, monitoring, backups."""
from __future__ import annotations

from agents.base import BaseAgent

SYSTEM_PROMPT = """You are the SysAdmin agent for AIDA OS.
You manage system services, Docker containers, VMs, monitoring, and backups.
You always confirm destructive operations before executing them.
You never delete storage pools or manage secrets.
"""


class SysadminAgent(BaseAgent):
    name = "sysadmin"

    async def handle(self, payload: dict) -> dict:
        task = payload.get("task", "")
        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ]
        )
        return {"agent": self.name, "response": response}
