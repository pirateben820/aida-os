"""AI recommender — given hardware + user answers, returns a UserProfile.

Uses a cloud AI (via LiteLLM) because local models are not installed yet.
Falls back to a rule-based recommendation if no cloud key is available.
"""
from __future__ import annotations

import json
import logging
import os

from aidad.hardware import HardwareInfo
from setup.profile import AgentSelections, DesktopPrefs, ModelSelections, UserProfile

log = logging.getLogger(__name__)

# All starter models with their sizes and best use-cases.
# Only models that fit within the 20 GB budget are listed here.
_MODEL_MENU = [
    {"id": "qwen2.5-coder:7b",   "skills": ["coding"],            "vram_gb": 5,  "size_gb": 4.7},
    {"id": "deepseek-r1:1.5b",   "skills": ["reasoning", "math"], "vram_gb": 2,  "size_gb": 1.1},
    {"id": "nomic-embed-text",   "skills": ["embedding"],          "vram_gb": 1,  "size_gb": 0.3},
    {"id": "qwen2.5:7b",         "skills": ["general", "planning"],"vram_gb": 5,  "size_gb": 4.7},
    {"id": "llava:7b",           "skills": ["vision"],             "vram_gb": 5,  "size_gb": 4.7},
]

_ALL_AGENTS = ["aida", "hermes", "archon", "sysadmin", "security", "research", "storage"]

_SYSTEM_PROMPT = """\
You are the AIDA OS setup assistant. Your job is to analyse this machine's hardware
and the user's answers, then return a JSON configuration that personalises the OS.

Rules:
- Only recommend models whose total size fits within the remaining disk budget.
- Always include nomic-embed-text (needed for Hermes memory).
- Always enable agents: aida, hermes.
- Enable additional agents only if relevant to stated use cases.
- Respect privacy_level: if "paranoid", set air_gapped=true and do not suggest cloud.
- Be concise in the "notes" field — one or two sentences max.

Return ONLY valid JSON matching this schema (no markdown, no explanation):
{
  "name": "<user name or empty string>",
  "use_cases": ["<use case>", ...],
  "skill_level": "beginner|intermediate|expert",
  "privacy_level": "standard|high|paranoid",
  "air_gapped": false,
  "language": "en",
  "desktop": {
    "environment": "hyprland|gnome|kde|sway|none",
    "terminal": "kitty|alacritty|foot|gnome-terminal",
    "theme": "dark|light",
    "layout": "tiling|floating"
  },
  "models": {"to_pull": ["<model_id>", ...]},
  "agents": {"enabled": ["<agent_name>", ...]},
  "notes": "<brief summary of user preferences>"
}
"""


def _hardware_summary(hw: HardwareInfo) -> str:
    gpu_info = (
        ", ".join(f"{g.name} ({g.vram_total_mb // 1024}GB VRAM)" for g in hw.gpus)
        or "no dedicated GPU (CPU inference only)"
    )
    return (
        f"CPU: {hw.cpu_cores} cores / {hw.cpu_threads} threads\n"
        f"RAM: {hw.ram_total_mb // 1024} GB\n"
        f"GPU: {gpu_info}"
    )


def _model_menu_summary() -> str:
    lines = []
    for m in _MODEL_MENU:
        lines.append(
            f"  {m['id']:30s}  {m['size_gb']} GB  skills={m['skills']}  vram_needed={m['vram_gb']}GB"
        )
    return "\n".join(lines)


async def ai_recommend(
    hardware: HardwareInfo,
    conversation: list[dict],
    cloud_model: str = "claude-haiku-4-5-20251001",
) -> UserProfile:
    """Ask the cloud AI to produce a UserProfile from the conversation."""
    try:
        import litellm

        hw_block = _hardware_summary(hardware)
        menu_block = _model_menu_summary()
        free_vram = hardware.free_vram_mb / 1024

        context = (
            f"Hardware:\n{hw_block}\n\n"
            f"Available VRAM for models: {free_vram:.1f} GB\n\n"
            f"Available models (stay under 12 GB total to fit in 20 GB OS budget):\n{menu_block}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "system", "content": context},
            *conversation,
        ]

        resp = await litellm.acompletion(
            model=cloud_model,
            messages=messages,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return UserProfile.model_validate(data)

    except Exception as exc:
        log.warning("Cloud AI recommendation failed (%s), using rule-based fallback", exc)
        return _rule_based_recommend(hardware, conversation)


def _rule_based_recommend(
    hardware: HardwareInfo, conversation: list[dict]
) -> UserProfile:
    """Simple rule-based fallback when no cloud AI is available."""
    text = " ".join(m.get("content", "") for m in conversation).lower()
    free_vram_gb = hardware.free_vram_mb / 1024

    use_cases = []
    if any(w in text for w in ["code", "coding", "develop", "program"]):
        use_cases.append("coding")
    if any(w in text for w in ["research", "study", "learn"]):
        use_cases.append("research")
    if any(w in text for w in ["server", "homelab", "docker", "sysadmin"]):
        use_cases.append("sysadmin")
    if any(w in text for w in ["game", "gaming", "play"]):
        use_cases.append("gaming")
    if not use_cases:
        use_cases = ["general"]

    to_pull = ["nomic-embed-text", "deepseek-r1:1.5b"]
    if free_vram_gb >= 5 or hardware.ram_free_mb // 1024 >= 8:
        to_pull.append("qwen2.5-coder:7b")
        if "research" in use_cases or "general" in use_cases:
            to_pull.append("qwen2.5:7b")

    enabled_agents = ["aida", "hermes"]
    if "coding" in use_cases:
        enabled_agents.append("archon")
    if "sysadmin" in use_cases:
        enabled_agents += ["sysadmin", "storage"]
    if "research" in use_cases:
        enabled_agents.append("research")
    enabled_agents.append("security")

    privacy = "paranoid" if "privacy" in text or "air" in text else "high"

    return UserProfile(
        use_cases=use_cases,
        privacy_level=privacy,
        air_gapped="air" in text,
        models=ModelSelections(to_pull=to_pull),
        agents=AgentSelections(enabled=list(dict.fromkeys(enabled_agents))),
        notes="Configured via rule-based fallback (no cloud AI available).",
    )
