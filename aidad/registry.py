"""Model Registry — loads models.yaml and answers scheduler queries."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).parent.parent / "config" / "models.yaml"


class ModelRequirements(BaseModel):
    vram_gb: float = 0
    min_ram_gb: float = 0


class ModelEntry(BaseModel):
    id: str
    provider: str
    skills: list[str] = Field(default_factory=list)
    context_length: int = 4096
    requirements: ModelRequirements = Field(default_factory=ModelRequirements)
    cloud: bool = False
    starter: bool = False


class ModelRegistry:
    def __init__(self, path: Path = _REGISTRY_PATH) -> None:
        self._models: list[ModelEntry] = []
        self._load(path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            log.warning("models.yaml not found at %s", path)
            return
        raw = yaml.safe_load(path.read_text())
        for entry in raw.get("models", []):
            self._models.append(ModelEntry.model_validate(entry))
        log.info("Loaded %d model(s) from registry", len(self._models))

    def all(self) -> list[ModelEntry]:
        return list(self._models)

    def by_skill(
        self,
        skill: str,
        max_vram_gb: float = 999,
        max_ram_gb: float = 999,
        allow_cloud: bool = True,
        local_first: bool = True,
    ) -> list[ModelEntry]:
        """Return models matching the skill, sorted local-first if requested."""
        candidates = [
            m
            for m in self._models
            if skill in m.skills
            and m.requirements.vram_gb <= max_vram_gb
            and m.requirements.min_ram_gb <= max_ram_gb
            and (allow_cloud or not m.cloud)
        ]
        if local_first:
            candidates.sort(key=lambda m: m.cloud)
        return candidates

    def get(self, model_id: str) -> Optional[ModelEntry]:
        return next((m for m in self._models if m.id == model_id), None)
