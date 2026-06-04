"""Self-Heal daemon — monitors the system and fixes problems automatically.

Alpha scope only:
  - Restart failed systemd services
  - Restart crashed Ollama
  - Free memory when pressure is critical
  - Fix broken Docker containers
  - Log every action taken so the user can review it

Run: python -m aidad.selfheal
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import psutil

log = logging.getLogger(__name__)

_ACTION_LOG = Path.home() / ".aida" / "selfheal.log"

# Services we are responsible for keeping alive
_WATCHED_SERVICES = [
    "aidad.service",
    "ollama.service",
    "docker.service",
    "NetworkManager.service",
    "nats",   # Docker container name
]

# Memory threshold — if available RAM drops below this, take action
_LOW_MEMORY_MB = 512

# How often to check (seconds)
_INTERVAL = 30


def _log_action(action: str, detail: str) -> None:
    _ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "ts": datetime.utcnow().isoformat(),
        "action": action,
        "detail": detail,
    })
    with _ACTION_LOG.open("a") as f:
        f.write(entry + "\n")
    log.info("[selfheal] %s — %s", action, detail)


def _service_is_failed(name: str) -> bool:
    if not shutil.which("systemctl"):
        return False
    result = subprocess.run(
        ["systemctl", "is-failed", "--quiet", name],
        capture_output=True,
    )
    return result.returncode == 0


def _restart_service(name: str) -> None:
    subprocess.run(["systemctl", "restart", name], capture_output=True)
    _log_action("restart_service", name)


def _docker_container_running(name: str) -> bool:
    if not shutil.which("docker"):
        return True   # can't check, assume ok
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", name],
        capture_output=True, text=True,
    )
    return result.stdout.strip() == "true"


def _restart_docker_container(name: str) -> None:
    subprocess.run(["docker", "restart", name], capture_output=True)
    _log_action("restart_container", name)


def _free_memory() -> None:
    """Drop page cache to reclaim memory."""
    try:
        Path("/proc/sys/vm/drop_caches").write_text("1")
        _log_action("drop_caches", "freed page cache due to low memory")
    except PermissionError:
        pass


def _check_disk_space() -> None:
    usage = psutil.disk_usage("/")
    free_gb = usage.free / (1024 ** 3)
    if free_gb < 1.0:
        _log_action(
            "low_disk_warning",
            f"Only {free_gb:.1f} GB free on /. Consider cleaning up old models.",
        )


async def heal_loop() -> None:
    log.info("Self-heal daemon started (interval=%ds)", _INTERVAL)
    while True:
        # Check systemd services
        for svc in _WATCHED_SERVICES:
            if svc.endswith(".service") and _service_is_failed(svc):
                log.warning("Service %s is failed — restarting", svc)
                _restart_service(svc)

        # Check NATS container (Docker)
        if shutil.which("docker") and not _docker_container_running("nats"):
            log.warning("NATS container not running — restarting")
            _restart_docker_container("nats")

        # Check memory pressure
        vm = psutil.virtual_memory()
        if vm.available // (1024 * 1024) < _LOW_MEMORY_MB:
            log.warning("Low memory (%d MB free) — dropping caches", vm.available // (1024 * 1024))
            _free_memory()

        # Check disk space
        _check_disk_space()

        await asyncio.sleep(_INTERVAL)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [selfheal] %(message)s",
    )
    asyncio.run(heal_loop())


if __name__ == "__main__":
    main()
