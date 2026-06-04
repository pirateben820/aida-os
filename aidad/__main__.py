"""Entry point: python -m aidad"""
import asyncio
import logging

from aidad.daemon import AidaDaemon
from aidad.settings import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    settings = load_settings()
    daemon = AidaDaemon(settings)
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
