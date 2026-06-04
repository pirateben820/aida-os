"""NATS bus client — connect, publish, subscribe.

All agents import this module.  The connection is a process-level singleton
so each agent process only opens one connection.

Subject convention:
    aida.agent.<agent_name>.<action>

Examples:
    aida.agent.archon.task_request
    aida.agent.hermes.memory_query
    aida.agent.sysadmin.service_restart
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

import nats
from nats.aio.client import Client as NatsClient

log = logging.getLogger(__name__)

_NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
_nc: NatsClient | None = None
_lock = asyncio.Lock()


async def get_connection() -> NatsClient:
    global _nc
    async with _lock:
        if _nc is None or not _nc.is_connected:
            _nc = await nats.connect(_NATS_URL)
            log.info("Connected to NATS at %s", _NATS_URL)
    return _nc


async def publish(subject: str, payload: dict[str, Any]) -> None:
    nc = await get_connection()
    await nc.publish(subject, json.dumps(payload).encode())


async def subscribe(
    subject: str,
    handler: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    nc = await get_connection()

    async def _cb(msg):
        try:
            data = json.loads(msg.data.decode())
            await handler(data)
        except Exception as exc:
            log.exception("Bus handler error on %s: %s", subject, exc)

    await nc.subscribe(subject, cb=_cb)
    log.info("Subscribed to %s", subject)


async def request(
    subject: str,
    payload: dict[str, Any],
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Publish a request and wait for a reply (NATS request/reply pattern)."""
    nc = await get_connection()
    msg = await nc.request(subject, json.dumps(payload).encode(), timeout=timeout)
    return json.loads(msg.data.decode())
