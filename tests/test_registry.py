"""Tests for the model registry and scheduler."""
from pathlib import Path

import pytest

from aidad.hardware import HardwareInfo
from aidad.registry import ModelRegistry
from aidad.scheduler import ScheduleRequest, Scheduler


@pytest.fixture
def registry():
    return ModelRegistry()


@pytest.fixture
def rich_hardware():
    return HardwareInfo(
        cpu_cores=8,
        cpu_threads=16,
        ram_total_mb=32768,
        ram_free_mb=20000,
        gpus=[],
    )


def test_registry_loads(registry):
    assert len(registry.all()) > 0


def test_skill_lookup_coding(registry):
    results = registry.by_skill("coding", max_vram_gb=999, max_ram_gb=999)
    assert any(m.id == "qwen2.5-coder:7b" for m in results)


def test_local_first_ordering(registry):
    results = registry.by_skill("coding", allow_cloud=True, local_first=True)
    assert results[0].cloud is False


def test_scheduler_selects_model(registry, rich_hardware):
    scheduler = Scheduler(registry, rich_hardware, local_first=True, air_gapped=False)
    result = scheduler.select(ScheduleRequest(skill="coding", agent="archon"))
    assert result is not None
    assert "coding" in result.model.skills


def test_scheduler_air_gapped_no_cloud(registry, rich_hardware):
    scheduler = Scheduler(registry, rich_hardware, local_first=True, air_gapped=True)
    result = scheduler.select(ScheduleRequest(skill="coding", agent="archon"))
    if result:
        assert result.model.cloud is False


def test_scheduler_no_vram_skips_large_models(registry):
    hw = HardwareInfo(
        cpu_cores=4,
        cpu_threads=8,
        ram_total_mb=8192,
        ram_free_mb=6000,
        gpus=[],
    )
    scheduler = Scheduler(registry, hw, local_first=True, air_gapped=True)
    result = scheduler.select(ScheduleRequest(skill="coding", agent="archon"))
    # With air-gapped + no VRAM, only CPU models (vram_gb=0) should match
    if result:
        assert result.model.requirements.vram_gb == 0
