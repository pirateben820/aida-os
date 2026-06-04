"""AIDA — primary OS assistant and task router."""
from __future__ import annotations

from agents.base import BaseAgent


SYSTEM_PROMPT = """You are AIDA, the AI-native operating system assistant.
You help the user manage their system, coordinate tasks, and route requests to the
correct specialist agent. You are concise, clear, and privacy-aware.
You never expose secrets or personal data to external services without user consent.
"""


class AidaAgent(BaseAgent):
    name = "aida"

    async def handle(self, payload: dict) -> dict:
        user_message = payload.get("message", "")
        self.log.info("Received message: %s", user_message[:80])

        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        return {"agent": self.name, "response": response}
