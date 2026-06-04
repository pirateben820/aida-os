"""User profile produced by the setup wizard and consumed by aidad + Hermes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

_PROFILE_PATH = Path.home() / ".aida" / "profile.yaml"


class DesktopPrefs(BaseModel):
    environment: str = "hyprland"     # e.g. hyprland, gnome, kde, sway, none
    terminal: str = "kitty"
    theme: str = "dark"
    layout: str = "tiling"            # tiling | floating


class ModelSelections(BaseModel):
    # model IDs to pull via Ollama after setup
    to_pull: list[str] = Field(default_factory=list)


class AgentSelections(BaseModel):
    enabled: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    name: str = ""
    use_cases: list[str] = Field(default_factory=list)   # coding, gaming, research, …
    skill_level: str = "intermediate"                     # beginner | intermediate | expert
    privacy_level: str = "high"                           # standard | high | paranoid
    air_gapped: bool = False
    language: str = "en"
    desktop: DesktopPrefs = Field(default_factory=DesktopPrefs)
    models: ModelSelections = Field(default_factory=ModelSelections)
    agents: AgentSelections = Field(default_factory=AgentSelections)
    notes: str = ""   # free-form AI summary of user preferences


def save_profile(profile: UserProfile, path: Path = _PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(profile.model_dump(), default_flow_style=False))


def load_profile(path: Path = _PROFILE_PATH) -> Optional[UserProfile]:
    if not path.exists():
        return None
    return UserProfile.model_validate(yaml.safe_load(path.read_text()))
