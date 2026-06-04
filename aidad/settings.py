"""Load and validate runtime settings."""
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class NatsSettings(BaseModel):
    url: str = "nats://127.0.0.1:4222"


class OllamaSettings(BaseModel):
    url: str = "http://127.0.0.1:11434"


class VllmSettings(BaseModel):
    url: str = ""
    enabled: bool = False


class DaemonSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8421
    log_level: str = "INFO"


class PrivacySettings(BaseModel):
    default_cloud_policy: str = "ask"
    air_gapped: bool = False


class BudgetSettings(BaseModel):
    monthly_usd: float = 0
    warn_at_percent: int = 80


class Settings(BaseModel):
    daemon: DaemonSettings = Field(default_factory=DaemonSettings)
    nats: NatsSettings = Field(default_factory=NatsSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    vllm: VllmSettings = Field(default_factory=VllmSettings)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)
    local_first: bool = True


_CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"


def load_settings(path: Path = _CONFIG_PATH) -> Settings:
    if path.exists():
        raw = yaml.safe_load(path.read_text())
        return Settings.model_validate(raw or {})
    return Settings()
