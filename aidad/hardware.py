"""Hardware inventory — CPU, RAM, GPU detection using existing system tools."""
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field

import psutil

log = logging.getLogger(__name__)


@dataclass
class GpuInfo:
    index: int
    name: str
    vram_total_mb: int
    vram_free_mb: int
    driver: str  # "nvidia" | "amd" | "unknown"


@dataclass
class HardwareInfo:
    cpu_cores: int
    cpu_threads: int
    ram_total_mb: int
    ram_free_mb: int
    gpus: list[GpuInfo] = field(default_factory=list)

    @property
    def total_vram_mb(self) -> int:
        return sum(g.vram_total_mb for g in self.gpus)

    @property
    def free_vram_mb(self) -> int:
        return sum(g.vram_free_mb for g in self.gpus)

    def to_dict(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "ram_total_mb": self.ram_total_mb,
            "ram_free_mb": self.ram_free_mb,
            "gpus": [g.__dict__ for g in self.gpus],
            "total_vram_mb": self.total_vram_mb,
            "free_vram_mb": self.free_vram_mb,
        }


def _detect_nvidia_gpus() -> list[GpuInfo]:
    if not shutil.which("nvidia-smi"):
        return []
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        )
        gpus = []
        for line in out.strip().splitlines():
            idx, name, total, free = [p.strip() for p in line.split(",")]
            gpus.append(
                GpuInfo(
                    index=int(idx),
                    name=name,
                    vram_total_mb=int(total),
                    vram_free_mb=int(free),
                    driver="nvidia",
                )
            )
        return gpus
    except Exception as exc:
        log.warning("nvidia-smi failed: %s", exc)
        return []


def _detect_amd_gpus() -> list[GpuInfo]:
    if not shutil.which("rocm-smi"):
        return []
    try:
        out = subprocess.check_output(
            ["rocm-smi", "--showmeminfo", "vram", "--json"],
            text=True,
            timeout=10,
        )
        data = json.loads(out)
        gpus = []
        for idx, (card, info) in enumerate(data.items()):
            total = int(info.get("VRAM Total Memory (B)", 0)) // (1024 * 1024)
            used = int(info.get("VRAM Total Used Memory (B)", 0)) // (1024 * 1024)
            gpus.append(
                GpuInfo(
                    index=idx,
                    name=card,
                    vram_total_mb=total,
                    vram_free_mb=total - used,
                    driver="amd",
                )
            )
        return gpus
    except Exception as exc:
        log.warning("rocm-smi failed: %s", exc)
        return []


def detect_hardware() -> HardwareInfo:
    vm = psutil.virtual_memory()
    gpus = _detect_nvidia_gpus() or _detect_amd_gpus()
    return HardwareInfo(
        cpu_cores=psutil.cpu_count(logical=False) or 1,
        cpu_threads=psutil.cpu_count(logical=True) or 1,
        ram_total_mb=vm.total // (1024 * 1024),
        ram_free_mb=vm.available // (1024 * 1024),
        gpus=gpus,
    )
