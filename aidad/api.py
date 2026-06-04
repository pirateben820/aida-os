"""FastAPI application — REST + WebSocket interface for aidad."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from pydantic import BaseModel

if TYPE_CHECKING:
    from aidad.daemon import AidaDaemon


class ScheduleRequestBody(BaseModel):
    skill: str
    agent: str
    require_local: bool = False


def build_app(daemon: "AidaDaemon") -> FastAPI:
    app = FastAPI(title="aidad", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/hardware")
    async def hardware():
        return daemon.hardware.to_dict()

    @app.get("/models")
    async def models():
        return [m.model_dump() for m in daemon.registry.all()]

    @app.post("/schedule")
    async def schedule(body: ScheduleRequestBody):
        from aidad.scheduler import ScheduleRequest

        req = ScheduleRequest(
            skill=body.skill,
            agent=body.agent,
            require_local=body.require_local,
        )
        result = daemon.scheduler.select(req)
        if result is None:
            return {"error": "no model available for requested skill"}
        return {
            "model": result.model.id,
            "provider": result.provider,
            "litellm_model_id": result.litellm_model_id,
        }

    # --- Seeder endpoints ---

    @app.get("/seeder/stats")
    async def seeder_stats():
        if daemon.seeder is None:
            return {"error": "seeder not available (install python-libtorrent)"}
        return daemon.seeder.stats()

    @app.post("/seeder/seed/{model_id:path}")
    async def seeder_seed(model_id: str):
        if daemon.seeder is None:
            return {"error": "seeder not available"}
        try:
            magnet = daemon.seeder.seed(model_id)
            return {"model": model_id, "magnet": magnet}
        except FileNotFoundError:
            return {"error": f"model '{model_id}' has not been pulled yet"}

    @app.get("/seeder/magnets")
    async def seeder_magnets():
        """Return the known magnet links from config/model_torrents.yaml."""
        import yaml
        from pathlib import Path

        registry_path = Path(__file__).parent.parent / "config" / "model_torrents.yaml"
        if not registry_path.exists():
            return {}
        return yaml.safe_load(registry_path.read_text()) or {}

    return app
