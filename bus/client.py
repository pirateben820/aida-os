"""NATS bus client — connect, publish, subscribe.

Subject convention:
    aida.agent.<agent_name>.request   ← agent listens here
    aida.agent.<agent_name>.<action>  ← fire-and-forget events

All agents use subscribe_reply() so callers get a response back.
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
from nats.aio.msg import Msg

log = logging.getLogger(__name__)

_NATS_URL = os.environ.get("NATS_URL", "nats://127.0.0.1:4222")
_nc: NatsClient | None = None
_lock = asyncio.Lock()


async def get_connection() -> NatsClient:
    global _nc
    async with _lock:
        if _nc is None or not _nc.is_connected:
            _nc = await nats.connect(
                _NATS_URL,
                error_cb=lambda e: log.error("NATS error: %s", e),
                disconnected_cb=lambda: log.warning("NATS disconnected"),
                reconnected_cb=lambda: log.info("NATS reconnected"),
            )
            log.info("Connected to NATS at %s", _NATS_URL)
    return _nc


async def publish(subject: str, payload: dict[str, Any]) -> None:
    nc = await get_connection()
    await nc.publish(subject, json.dumps(payload).encode())


async def subscribe_reply(
    subject: str,
    handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
) -> None:
    """Subscribe and automatically reply — use this for all agent request handlers.

    The handler receives the decoded payload dict and must return a dict.
    If the message has a reply subject, the return value is sent back.
    """
    nc = await get_connection()

    async def _cb(msg: Msg) -> None:
        try:
            data = json.loads(msg.data.decode())
            result = await handler(data)
            if msg.reply:
                await msg.respond(json.dumps(result).encode())
        except Exception as exc:
            log.exception("Bus handler error on %s: %s", subject, exc)
            if msg.reply:
                await msg.respond(json.dumps({"error": str(exc)}).encode())

    await nc.subscribe(subject, cb=_cb)
    log.info("Subscribed to %s", subject)


async def subscribe(
    subject: str,
    handler: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    """Fire-and-forget subscribe — no reply sent."""
    nc = await get_connection()

    async def _cb(msg: Msg) -> None:
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
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Send a request and wait for a reply."""
    nc = await get_connection()
    msg = await nc.request(subject, json.dumps(payload).encode(), timeout=timeout)
    return json.loads(msg.data.decode())
