"""Archon — coding harness agent."""
from __future__ import annotations

from agents.base import BaseAgent

SYSTEM_PROMPT = """You are Archon, a software engineering agent.
You write, review, test, and deploy code. You have access to the filesystem
and can run sandboxed shell commands. You always follow secure coding practices.
Never execute commands that could damage the system or leak secrets.
"""


class ArchonAgent(BaseAgent):
    name = "archon"

    async def handle(self, payload: dict) -> dict:
        task = payload.get("task", "")
        context = payload.get("context", "")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": task})

        response = await self.chat(messages=messages, skill="coding")
        return {"agent": self.name, "response": response}
