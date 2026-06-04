"""AidaDaemon — main process that wires everything together."""
from __future__ import annotations

import asyncio
import logging

import uvicorn

from aidad.api import build_app
from aidad.hardware import detect_hardware
from aidad.registry import ModelRegistry
from aidad.scheduler import Scheduler
from aidad.settings import Settings

log = logging.getLogger(__name__)


class AidaDaemon:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.hardware = detect_hardware()
        self.registry = ModelRegistry()
        self.scheduler = Scheduler(
            registry=self.registry,
            hardware=self.hardware,
            local_first=settings.local_first,
            air_gapped=settings.privacy.air_gapped,
        )
        self.seeder = self._init_seeder()
        self.app = build_app(self)

    def _init_seeder(self):
        try:
            from seeder.seeder import ModelSeeder
            return ModelSeeder()
        except ImportError:
            log.warning("libtorrent not installed — model seeding disabled")
            return None

    async def _start_seeding_installed_models(self) -> None:
        """Seed every starter model that Ollama has already pulled."""
        if self.seeder is None:
            return
        for model in self.registry.all():
            if model.cloud or not model.starter:
                continue
            try:
                magnet = self.seeder.seed(model.id)
                log.info("Seeding %s  magnet=%s", model.id, magnet[:60])
            except FileNotFoundError:
                log.debug("Model %s not pulled yet, skipping seed", model.id)
            except Exception as exc:
                log.warning("Could not seed %s: %s", model.id, exc)

    async def run(self) -> None:
        log.info("Hardware: %s", self.hardware.to_dict())
        log.info("Models in registry: %d", len(self.registry.all()))

        asyncio.create_task(self._start_seeding_installed_models())

        # Start self-improve loop inside the daemon process
        from aidad.selfimprove import improve_loop
        asyncio.create_task(improve_loop())

        config = uvicorn.Config(
            app=self.app,
            host=self.settings.daemon.host,
            port=self.settings.daemon.port,
            log_level=self.settings.daemon.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
