"""Installer — applies a UserProfile to the system.

Pulls Ollama models (via torrent first, direct download fallback),
installs the desktop environment, and writes aidad config.
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
from pathlib import Path

from setup.profile import UserProfile, save_profile

log = logging.getLogger(__name__)

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
_TORRENT_REGISTRY = Path(__file__).parent.parent / "config" / "model_torrents.yaml"


async def _pull_model_torrent(model_id: str, print_fn) -> bool:
    """Try to get the model via P2P torrent. Returns True on success."""
    try:
        import yaml
        from seeder.seeder import ModelSeeder

        if not _TORRENT_REGISTRY.exists():
            return False
        registry = yaml.safe_load(_TORRENT_REGISTRY.read_text()) or {}
        magnet = registry.get("magnets", {}).get(model_id)
        if not magnet:
            return False

        print_fn(f"  Downloading {model_id} via torrent (P2P)…")
        seeder = ModelSeeder()
        handle = seeder.download(magnet)
        await seeder.wait_for_download(handle)
        return True
    except Exception as exc:
        log.debug("Torrent download failed for %s: %s", model_id, exc)
        return False


async def _pull_model_ollama(model_id: str, print_fn) -> None:
    """Pull model directly from Ollama registry."""
    print_fn(f"  Downloading {model_id} from Ollama…")
    proc = await asyncio.create_subprocess_exec(
        "ollama", "pull", model_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert proc.stdout
    async for line in proc.stdout:
        text = line.decode().strip()
        if text:
            print_fn(f"    {text}")
    await proc.wait()


async def pull_models(profile: UserProfile, print_fn=print) -> None:
    """Pull all models in the profile — torrent first, Ollama fallback."""
    for model_id in profile.models.to_pull:
        print_fn(f"\n[model] {model_id}")
        ok = await _pull_model_torrent(model_id, print_fn)
        if not ok:
            await _pull_model_ollama(model_id, print_fn)
        print_fn(f"  ✓ {model_id} ready")


def _install_desktop(profile: UserProfile, print_fn=print) -> None:
    env = profile.desktop.environment
    if env == "none":
        print_fn("[desktop] Skipping desktop environment (none selected)")
        return

    packages = {
        "hyprland": ["hyprland", "waybar", "wofi", "kitty", "hyprpaper"],
        "sway":     ["sway", "waybar", "wofi", "foot", "swww"],
        "gnome":    ["gnome", "gnome-terminal"],
        "kde":      ["plasma", "konsole", "dolphin"],
    }.get(env, [])

    if not packages:
        print_fn(f"[desktop] Unknown environment '{env}', skipping")
        return

    terminal_pkg = profile.desktop.terminal
    if terminal_pkg not in packages:
        packages.append(terminal_pkg)

    print_fn(f"[desktop] Installing {env}: {' '.join(packages)}")
    if shutil.which("pacman"):
        subprocess.run(
            ["sudo", "pacman", "-S", "--needed", "--noconfirm"] + packages,
            check=False,
        )
    else:
        print_fn("  (pacman not found — skipping package install, dev mode)")


def _write_aidad_config(profile: UserProfile) -> None:
    import yaml

    if not _SETTINGS_PATH.exists():
        return
    settings = yaml.safe_load(_SETTINGS_PATH.read_text()) or {}
    settings["privacy"]["air_gapped"] = profile.air_gapped
    if profile.privacy_level == "paranoid":
        settings["privacy"]["default_cloud_policy"] = "never"
    _SETTINGS_PATH.write_text(yaml.dump(settings, default_flow_style=False))


async def apply_profile(profile: UserProfile, print_fn=print) -> None:
    """Apply a UserProfile: install desktop, pull models, update config."""
    print_fn("\n=== Applying your AIDA OS configuration ===\n")

    _install_desktop(profile, print_fn)
    await pull_models(profile, print_fn)
    _write_aidad_config(profile)
    save_profile(profile)

    print_fn("\n✓ Setup complete. Your profile has been saved to ~/.aida/profile.yaml")
    print_fn("  Start AIDA OS: python -m aidad\n")
