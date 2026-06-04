"""Storage agent — capacity monitoring, backups, data organisation."""
from __future__ import annotations

from agents.base import BaseAgent

SYSTEM_PROMPT = """You are the Storage agent for AIDA OS.
You manage storage capacity, backups, and data organisation.
You can read file metadata but NOT file contents.
You have no external network access.
"""


class StorageAgent(BaseAgent):
    name = "storage"

    async def handle(self, payload: dict) -> dict:
        task = payload.get("task", "")
        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            require_local=True,
        )
        return {"agent": self.name, "response": response}
