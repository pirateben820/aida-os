"""Research agent — internet search and documentation lookup."""
from __future__ import annotations

from agents.base import BaseAgent

SYSTEM_PROMPT = """You are the Research agent for AIDA OS.
You search the internet for information, look up documentation, and summarise findings.
You have read-only internet access. You cannot read local files or run commands.
Always cite your sources.
"""


class ResearchAgent(BaseAgent):
    name = "research"

    async def handle(self, payload: dict) -> dict:
        query = payload.get("query", "")
        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]
        )
        return {"agent": self.name, "response": response}
