"""First-boot setup wizard.

Run:  python -m setup.wizard
  or: aida-setup   (after pip install -e .)
"""
from __future__ import annotations

import asyncio
import os
import sys
import webbrowser

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    _RICH = True
except ImportError:
    _RICH = False

from aidad.hardware import detect_hardware
from setup.installer import apply_profile
from setup.profile import load_profile
from setup.providers import FREE_PROVIDERS, FreeProvider, already_configured, get_provider
from setup.recommender import ai_recommend

console = Console() if _RICH else None


# ── helpers ──────────────────────────────────────────────────────────────────

def _print(text: str = "", style: str = "") -> None:
    if _RICH and console:
        console.print(text, style=style or None)
    else:
        import re
        print(re.sub(r"\[/?[a-z_ ]+\]", "", text))   # strip rich tags


def _input(prompt: str) -> str:
    if _RICH and console:
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]")
    return input(f"{prompt}: ")


def _banner() -> None:
    lines = [
        "    ░█████╗░██╗██████╗░░█████╗░     ░█████╗░░██████╗",
        "    ██╔══██╗██║██╔══██╗██╔══██╗    ██╔══██╗██╔════╝",
        "    ███████║██║██║  ██║███████║    ██║  ██║╚█████╗░",
        "    ██╔══██║██║██║  ██║██╔══██║    ██║  ██║░╚═══██╗",
        "    ██║  ██║██║██████╔╝██║  ██║    ╚█████╔╝██████╔╝",
        "    ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝    ╚════╝ ╚═════╝",
    ]
    art = "\n".join(lines)
    if _RICH and console:
        console.print(Panel(art, subtitle="[bold]AI-Native Operating System — First Boot Setup[/bold]", style="bold blue"))
    else:
        print(art)
        print("\n  AIDA OS — First Boot Setup\n")


# ── provider selection ────────────────────────────────────────────────────────

def _show_provider_table() -> None:
    if _RICH and console:
        t = Table(show_header=True, header_style="bold magenta")
        t.add_column("#",         style="dim", width=3)
        t.add_column("Provider",  style="bold")
        t.add_column("Free tier")
        t.add_column("Get key at", style="dim")
        for i, p in enumerate(FREE_PROVIDERS, 1):
            t.add_row(str(i), p.name, p.free_note, p.get_key_url)
        console.print(t)
    else:
        for i, p in enumerate(FREE_PROVIDERS, 1):
            print(f"  {i}. {p.name}")
            print(f"     {p.free_note}")
            print(f"     {p.get_key_url}")
            print()


def _select_provider() -> FreeProvider:
    """Let the user pick a provider, or detect one already configured."""
    # Auto-detect existing key
    found = already_configured()
    if found:
        _print(f"\n[green]Found API key for {found.name} — using it for setup.[/green]")
        return found

    _print("\n[bold]Choose a free AI provider for this setup session.[/bold]")
    _print("After setup your local models take over — you won't need this key again.\n")
    _show_provider_table()

    while True:
        choice = _input("Enter number or short name (e.g. gemini, groq, openrouter)").strip().lower()

        # accept number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(FREE_PROVIDERS):
                return FREE_PROVIDERS[idx]

        # accept short key
        p = get_provider(choice)
        if p:
            return p

        _print("[red]Invalid choice, try again.[/red]")


def _get_api_key(provider: FreeProvider) -> str:
    """Get the API key — from env, or ask the user."""
    existing = os.environ.get(provider.env_var, "")
    if existing:
        return existing

    _print(f"\n[bold]{provider.name}[/bold] — get a free key at:")
    _print(f"  [link]{provider.get_key_url}[/link]" if _RICH else f"  {provider.get_key_url}")

    open_browser = _input("Open that URL in your browser now? (yes/no)").strip().lower()
    if open_browser in ("yes", "y"):
        webbrowser.open(provider.get_key_url)
        _print("Opened. Paste your API key below when ready.")

    key = _input(f"Paste your {provider.env_var}").strip()
    os.environ[provider.env_var] = key
    return key


# ── conversation questions ────────────────────────────────────────────────────

_QUESTIONS = [
    ("name",      "What's your name?"),
    ("use_cases", "What will you mainly use this computer for?\n"
                  "  (e.g. coding, research, gaming, home server, creative work — or just describe it)"),
    ("skill",     "How would you describe your technical skill level? (beginner / intermediate / expert)"),
    ("privacy",   "How important is privacy?\n"
                  "  standard  — cloud AI can help with everyday tasks\n"
                  "  high      — ask before sending anything personal to the cloud\n"
                  "  paranoid  — local AI only, never connect to cloud"),
    ("desktop",   "Do you prefer a tiling window manager (Hyprland / Sway) "
                  "or a traditional desktop (GNOME / KDE)?"),
    ("theme",     "Dark or light theme?"),
    ("extra",     "Anything else you'd like AIDA to know about how you work or what you need?"),
]


# ── main wizard ───────────────────────────────────────────────────────────────

async def run_wizard() -> None:
    _banner()

    if load_profile() is not None:
        _print("\n[yellow]AIDA OS is already configured.[/yellow]")
        redo = _input("Run setup again? (yes/no)")
        if redo.strip().lower() not in ("yes", "y"):
            return

    # Hardware scan
    _print("\n[bold]Scanning your hardware…[/bold]\n")
    hardware = detect_hardware()
    _print(f"  CPU   {hardware.cpu_cores} cores / {hardware.cpu_threads} threads")
    _print(f"  RAM   {hardware.ram_total_mb // 1024} GB")
    if hardware.gpus:
        for g in hardware.gpus:
            _print(f"  GPU   {g.name}  {g.vram_total_mb // 1024} GB VRAM")
    else:
        _print("  GPU   none (will use CPU inference)")

    # Provider selection
    provider = _select_provider()
    api_key  = _get_api_key(provider)

    if not api_key:
        _print("\n[yellow]No API key provided — falling back to rule-based setup.[/yellow]")
        cloud_model = None
    else:
        cloud_model = provider.litellm_model
        _print(f"\n[green]Using {provider.name} for this setup session.[/green]")

    # Conversation
    _print("\n[bold]A few quick questions and AIDA will configure everything for you.[/bold]\n")
    conversation: list[dict] = []

    for _key, question in _QUESTIONS:
        _print(f"\n[bold cyan]AIDA:[/bold cyan] {question}" if _RICH
               else f"\nAIDA: {question}")
        answer = _input("You").strip()
        if answer:
            conversation.append({"role": "assistant", "content": question})
            conversation.append({"role": "user",      "content": answer})

    # AI recommendation
    _print("\n[bold]Analysing your answers…[/bold]\n")
    profile = await ai_recommend(
        hardware=hardware,
        conversation=conversation,
        cloud_model=cloud_model or "gemini/gemini-1.5-flash",
    )

    # Show plan
    _print("\n[bold]Here is what AIDA will set up for you:[/bold]\n")
    _print(f"  Use cases    {', '.join(profile.use_cases)}")
    _print(f"  Skill level  {profile.skill_level}")
    _print(f"  Privacy      {profile.privacy_level}" + ("  (air-gapped)" if profile.air_gapped else ""))
    _print(f"  Desktop      {profile.desktop.environment} / {profile.desktop.theme} theme")
    _print(f"  Models       {', '.join(profile.models.to_pull)}")
    _print(f"  Agents       {', '.join(profile.agents.enabled)}")
    if profile.notes:
        _print(f"  Notes        {profile.notes}")

    _print()
    confirm = _input("Apply this configuration? (yes/no)")
    if confirm.strip().lower() not in ("yes", "y"):
        _print("Setup cancelled. Run 'aida-setup' to try again.")
        return

    await apply_profile(profile, print_fn=_print)
    _print("\n[bold green]Welcome to AIDA OS.[/bold green]" if _RICH else "\nWelcome to AIDA OS.")


def main() -> None:
    asyncio.run(run_wizard())


if __name__ == "__main__":
    main()
