"""aida-chat — terminal interface to talk to AIDA.

Sends messages through the NATS bus to the AIDA agent.
Falls back to direct MPI call if NATS is unavailable (dev mode).

Run: python -m aidad.chat
  or: aida-chat
"""
from __future__ import annotations

import asyncio
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

_SELFHEAL_LOG = Path.home() / ".aida" / "selfheal.log"
_IMPROVE_LOG  = Path.home() / ".aida" / "improvements.log"


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
    return (
        f"--- Current system state ---\n{system}\n"
        f"--- Recent self-heal actions ---\n{_tail_log(_SELFHEAL_LOG)}\n"
        f"--- Recent self-improve suggestions ---\n{_tail_log(_IMPROVE_LOG)}\n"
    )


def _print(text: str = "", style: str = "") -> None:
    if _RICH and console:
        if style:
            console.print(text, style=style)
        else:
            console.print(Markdown(text))
    else:
        import re
        print(re.sub(r"\[/?[a-z_ ]+\]", "", text))


def _input(prompt: str) -> str:
    if _RICH and console:
        return Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]")
    return input(f"{prompt}: ")


def _ssh_hint() -> str:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"  From your main machine:  ssh aida@{ip}"
    except Exception:
        return ""


async def _ask_aida(user_input: str, history: list[dict]) -> str:
    """Send a message to AIDA via the bus, fall back to direct call."""
    context = _build_context()
    payload = {
        "message": user_input,
        "system_context": context,
        "history": history,
    }
    try:
        from bus.client import request as bus_request
        result = await bus_request("aida.agent.aida.request", payload, timeout=60.0)
        return result.get("response", "(no response)")
    except Exception:
        # NATS not available — call agent directly (dev / no-bus mode)
        from agents.orchestrator import graph
        result = await graph.ainvoke({
            "user_message": user_input,
            "system_context": context,
            "memories": [],
            "response": "",
        })
        return result["response"]


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

        _print("\n[bold green]AIDA:[/bold green]" if _RICH else "\nAIDA:")
        try:
            response = await _ask_aida(user_input, history)
            _print(response)
        except Exception as exc:
            _print(f"[red]Error: {exc}[/red]" if _RICH else f"Error: {exc}")
            continue

        history.append({"role": "user",      "content": user_input})
        history.append({"role": "assistant", "content": response})
        if len(history) > 20:
            history = history[-20:]

        _print("")


def main() -> None:
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
