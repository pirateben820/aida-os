"""AI Scheduler — matches tasks to models based on skill + available resources."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from aidad.hardware import HardwareInfo
from aidad.registry import ModelEntry, ModelRegistry

log = logging.getLogger(__name__)


@dataclass
class ScheduleRequest:
    skill: str
    agent: str
    context_tokens: int = 0
    require_local: bool = False


@dataclass
class ScheduleResult:
    model: ModelEntry
    provider: str
    litellm_model_id: str  # format expected by LiteLLM


# Map registry provider names → LiteLLM prefix
_PROVIDER_PREFIX: dict[str, str] = {
    "ollama": "ollama/",
    "openai": "",
    "anthropic": "",
    "vllm": "openai/",  # vLLM exposes an OpenAI-compatible API
}


def _litellm_id(model: ModelEntry) -> str:
    prefix = _PROVIDER_PREFIX.get(model.provider, "")
    return f"{prefix}{model.id}"


class Scheduler:
    def __init__(
        self,
        registry: ModelRegistry,
        hardware: HardwareInfo,
        local_first: bool = True,
        air_gapped: bool = False,
    ) -> None:
        self._registry = registry
        self._hardware = hardware
        self._local_first = local_first
        self._air_gapped = air_gapped

    def select(self, req: ScheduleRequest) -> Optional[ScheduleResult]:
        free_vram_gb = self._hardware.free_vram_mb / 1024
        free_ram_gb = self._hardware.ram_free_mb / 1024
        allow_cloud = not self._air_gapped and not req.require_local

        candidates = self._registry.by_skill(
            skill=req.skill,
            max_vram_gb=free_vram_gb,
            max_ram_gb=free_ram_gb,
            allow_cloud=allow_cloud,
            local_first=self._local_first,
        )

        if not candidates:
            log.warning(
                "No model found for skill=%s vram=%.1fGB ram=%.1fGB cloud=%s",
                req.skill,
                free_vram_gb,
                free_ram_gb,
                allow_cloud,
            )
            return None

        chosen = candidates[0]
        log.info(
            "Scheduled agent=%s skill=%s → model=%s (provider=%s)",
            req.agent,
            req.skill,
            chosen.id,
            chosen.provider,
        )

        # Record usage for self-improve daemon
        try:
            from aidad.selfimprove import record_usage
            record_usage("model_used",   {"model": chosen.id, "skill": req.skill})
            record_usage("agent_invoked", {"agent": req.agent})
        except Exception:
            pass

        return ScheduleResult(
            model=chosen,
            provider=chosen.provider,
            litellm_model_id=_litellm_id(chosen),
        )
