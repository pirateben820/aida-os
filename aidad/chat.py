"""aida-chat — terminal interface to talk to AIDA.

Alpha scope: system-focused only.
AIDA can answer questions about what it is doing, what it fixed,
what models are running, and how to improve the system.
It cannot do general tasks in alpha.

Run: python -m aidad.chat
  or: aida-chat
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None

from mpi.client import mpi_chat

_SELFHEAL_LOG  = Path.home() / ".aida" / "selfheal.log"
_IMPROVE_LOG   = Path.home() / ".aida" / "improvements.log"
_USAGE_LOG     = Path.home() / ".aida" / "usage.jsonl"
_PROFILE       = Path.home() / ".aida" / "profile.yaml"

_ALPHA_SYSTEM_PROMPT = """You are AIDA, the AI built into AIDA OS.

This is alpha. Your only jobs right now are:
1. Tell the user what is happening on their system
2. Explain what you have fixed or improved
3. Answer questions about system health, models, and services
4. Suggest what the user can do to improve their setup

Do NOT pretend you can do general tasks like writing code, searching the web,
or managing files — those agents are not active in alpha.
Be honest, direct, and concise. If you don't know something, say so.
"""


def _tail_log(path: Path, n: int = 20) -> str:
    if not path.exists():
        return "(no entries yet)"
    lines = path.read_text().splitlines()
    return "\n".join(lines[-n:]) or "(empty)"


def _build_context() -> str:
    import psutil
    vm = psutil.virtual_memory()
    du = psutil.disk_usage("/")

    system = (
        f"RAM: {vm.used // (1024**2)} MB used / {vm.total // (1024**2)} MB total\n"
        f"Disk: {du.used // (1024**3)} GB used / {du.total // (1024**3)} GB total\n"
        f"CPU: {psutil.cpu_percent(interval=1):.0f}% used\n"
    )

    heal = _tail_log(_SELFHEAL_LOG)
    improve = _tail_log(_IMPROVE_LOG)

    return (
        f"--- Current system state ---\n{system}\n"
        f"--- Recent self-heal actions ---\n{heal}\n"
        f"--- Recent self-improve suggestions ---\n{improve}\n"
    )


def _print(text: str, style: str = "") -> None:
    if _RICH and console:
        if style:
            console.print(text, style=style)
        else:
            console.print(Markdown(text))
    else:
        print(text)


def _input(prompt: str) -> str:
    if _RICH and console:
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]")
    return input(f"{prompt}: ")


def _ssh_hint() -> str:
    """Return the ssh aida@<ip> hint if we can find the local IP."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"  From your main machine:  ssh aida@{ip}"
    except Exception:
        return ""


async def chat_loop() -> None:
    hint = _ssh_hint()
    if _RICH:
        _print("\n[bold blue]AIDA OS[/bold blue] — system assistant (alpha)")
        if hint:
            _print(f"[dim]{hint}[/dim]")
        _print("Type [bold]exit[/bold] to quit.\n")
    else:
        print("\nAIDA OS — system assistant (alpha)")
        if hint:
            print(hint)
        print("Type 'exit' to quit.\n")

    history: list[dict] = []

    while True:
        try:
            user_input = _input("You")
        except (EOFError, KeyboardInterrupt):
            _print("\nGoodbye.")
            break

        if user_input.strip().lower() in ("exit", "quit", "q"):
            _print("Goodbye.")
            break

        if not user_input.strip():
            continue

        context = _build_context()
        messages = [
            {"role": "system", "content": _ALPHA_SYSTEM_PROMPT},
            {"role": "system", "content": context},
            *history,
            {"role": "user", "content": user_input},
        ]

        _print("\n[bold green]AIDA:[/bold green] " if _RICH else "\nAIDA: ", style="")
        try:
            response = await mpi_chat(
                skill="general",
                agent="aida",
                messages=messages,
            )
            _print(response)
        except Exception as exc:
            _print(f"[red]Error: {exc}[/red]" if _RICH else f"Error: {exc}")
            continue

        history.append({"role": "user",      "content": user_input})
        history.append({"role": "assistant", "content": response})

        # Keep history short — last 10 exchanges
        if len(history) > 20:
            history = history[-20:]

        _print("")


def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
