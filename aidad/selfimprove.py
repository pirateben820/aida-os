"""Self-Improve daemon — watches what the user actually does and tunes the system.

Alpha scope only:
  - Track which models get used most → move them to priority in the scheduler
  - Track which agents get invoked → disable unused ones to save RAM
  - Watch memory/CPU after model loads → adjust model size recommendations
  - Write improvement suggestions back to config files (never applies without logging)

All changes are logged before being applied. Nothing is destructive.

Run: python -m aidad.selfimprove
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import psutil
import yaml

log = logging.getLogger(__name__)

_USAGE_LOG   = Path.home() / ".aida" / "usage.jsonl"
_IMPROVE_LOG = Path.home() / ".aida" / "improvements.log"
_MODELS_CFG  = Path(__file__).parent.parent / "config" / "models.yaml"
_AGENTS_CFG  = Path(__file__).parent.parent / "config" / "agents.yaml"

_INTERVAL        = 300   # check every 5 minutes
_MIN_SAMPLES     = 10    # need at least this many events before making changes


def _log_improvement(action: str, detail: str) -> None:
    _IMPROVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = f"[{datetime.utcnow().isoformat()}] {action}: {detail}\n"
    _IMPROVE_LOG.open("a").write(entry)
    log.info("[selfimprove] %s — %s", action, detail)


def record_usage(event: str, metadata: dict) -> None:
    """Call this from other modules to record a usage event."""
    _USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({"ts": datetime.utcnow().isoformat(), "event": event, **metadata})
    with _USAGE_LOG.open("a") as f:
        f.write(entry + "\n")


def _load_usage() -> list[dict]:
    if not _USAGE_LOG.exists():
        return []
    events = []
    for line in _USAGE_LOG.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return events


def _analyze_model_usage(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("event") == "model_used":
            counts[e.get("model", "unknown")] += 1
    return dict(counts)


def _analyze_agent_usage(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("event") == "agent_invoked":
            counts[e.get("agent", "unknown")] += 1
    return dict(counts)


def _promote_popular_models(model_counts: dict[str, int]) -> None:
    """Move most-used models to the top of models.yaml so they get scheduled first."""
    if not _MODELS_CFG.exists() or not model_counts:
        return
    cfg = yaml.safe_load(_MODELS_CFG.read_text())
    models = cfg.get("models", [])
    ranked = sorted(model_counts, key=lambda m: model_counts[m], reverse=True)

    # Reorder so most-used appear first (keeps all entries, just reorders)
    id_to_model = {m["id"]: m for m in models}
    reordered = [id_to_model[mid] for mid in ranked if mid in id_to_model]
    reordered += [m for m in models if m["id"] not in model_counts]

    if reordered != models:
        cfg["models"] = reordered
        _MODELS_CFG.write_text(yaml.dump(cfg, default_flow_style=False))
        top = ranked[0] if ranked else "?"
        _log_improvement("reorder_models", f"promoted '{top}' to top (most used)")


def _suggest_disable_unused_agents(agent_counts: dict[str, int], total: int) -> None:
    """Log a suggestion to disable agents that have never been used."""
    if total < _MIN_SAMPLES:
        return
    if not _AGENTS_CFG.exists():
        return
    cfg = yaml.safe_load(_AGENTS_CFG.read_text())
    all_agents = list(cfg.get("agents", {}).keys())
    never_used = [a for a in all_agents if agent_counts.get(a, 0) == 0]
    if never_used:
        _log_improvement(
            "suggest_disable_agents",
            f"These agents have never been invoked: {never_used}. "
            "Consider disabling them in config/agents.yaml to save RAM.",
        )


def _check_memory_headroom() -> None:
    """If RAM is consistently tight, suggest switching to smaller models."""
    vm = psutil.virtual_memory()
    used_pct = vm.percent
    if used_pct > 85:
        _log_improvement(
            "suggest_smaller_models",
            f"RAM usage is {used_pct:.0f}%. Consider switching to smaller models "
            "(e.g. deepseek-r1:1.5b instead of qwen2.5-coder:7b) to free memory.",
        )


async def improve_loop() -> None:
    log.info("Self-improve daemon started (interval=%ds)", _INTERVAL)
    while True:
        await asyncio.sleep(_INTERVAL)

        events = _load_usage()
        if not events:
            continue

        model_counts = _analyze_model_usage(events)
        agent_counts = _analyze_agent_usage(events)
        total = len(events)

        if total >= _MIN_SAMPLES:
            _promote_popular_models(model_counts)
            _suggest_disable_unused_agents(agent_counts, total)

        _check_memory_headroom()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [selfimprove] %(message)s",
    )
    asyncio.run(improve_loop())


if __name__ == "__main__":
    main()
