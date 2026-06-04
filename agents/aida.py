"""AIDA — primary OS assistant. Uses LangGraph to orchestrate other agents."""
from __future__ import annotations

from agents.base import BaseAgent


class AidaAgent(BaseAgent):
    name = "aida"

    async def handle(self, payload: dict) -> dict:
        from agents.orchestrator import graph

        user_message = payload.get("message", "")
        system_context = payload.get("system_context", "")
        history = payload.get("history", [])

        self.log.info("Received: %s", user_message[:80])

        result = await graph.ainvoke({
            "user_message": user_message,
            "system_context": system_context,
            "memories": [],
            "response": "",
        })
        return {"agent": self.name, "response": result["response"]}
