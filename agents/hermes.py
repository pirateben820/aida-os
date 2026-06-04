"""Hermes — personal assistant with long-term memory (ChromaDB, local-only)."""
from __future__ import annotations

import logging
from pathlib import Path

from agents.base import BaseAgent

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Hermes, a private personal assistant.
You help the user track projects, preferences, reminders, and history.
All data stays local. You never share personal information externally.
"""

_MEMORY_DIR = Path.home() / ".aida" / "hermes" / "memory"


class HermesAgent(BaseAgent):
    name = "hermes"

    def __init__(self) -> None:
        super().__init__()
        self._collection = self._init_memory()

    def _init_memory(self):
        try:
            import chromadb

            _MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(_MEMORY_DIR))
            return client.get_or_create_collection("hermes_memory")
        except Exception as exc:
            log.warning("ChromaDB unavailable, memory disabled: %s", exc)
            return None

    def remember(self, text: str, doc_id: str, metadata: dict | None = None) -> None:
        self.require("write_user_memory")
        if self._collection is None:
            return
        self._collection.upsert(
            documents=[text],
            ids=[doc_id],
            metadatas=[metadata or {}],
        )

    def recall(self, query: str, n: int = 5) -> list[str]:
        self.require("read_user_memory")
        if self._collection is None:
            return []
        results = self._collection.query(query_texts=[query], n_results=n)
        return results.get("documents", [[]])[0]

    async def handle(self, payload: dict) -> dict:
        action = payload.get("action", "chat")

        if action == "remember":
            self.remember(
                text=payload["text"],
                doc_id=payload["id"],
                metadata=payload.get("metadata"),
            )
            return {"status": "stored"}

        if action == "recall":
            docs = self.recall(payload.get("query", ""), n=payload.get("n", 5))
            return {"memories": docs}

        # Default: chat with memory context injected
        query = payload.get("message", "")
        memories = self.recall(query)
        memory_context = "\n".join(f"- {m}" for m in memories)
        response = await self.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "system",
                    "content": f"Relevant memories:\n{memory_context}" if memory_context else "",
                },
                {"role": "user", "content": query},
            ]
        )
        return {"agent": self.name, "response": response}
