"""Model seeder — creates torrents from pulled Ollama models and seeds them.

After a model is pulled via Ollama, call seed_model() to:
  1. Locate the model blobs in ~/.ollama/models/
  2. Create a .torrent file for them
  3. Start seeding via libtorrent (DHT, no tracker required)

Other AIDA OS nodes discover torrents through DHT and the shared magnet
links stored in config/model_torrents.yaml.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

import libtorrent as lt

log = logging.getLogger(__name__)

_OLLAMA_MODELS_DIR = Path.home() / ".ollama" / "models"
_TORRENTS_DIR = Path.home() / ".aida" / "torrents"
_TORRENT_REGISTRY = Path(__file__).parent.parent / "config" / "model_torrents.yaml"


def _blob_paths_for_model(model_id: str) -> list[Path]:
    """Return the blob files Ollama stored for this model.

    Ollama stores blobs as content-addressed files under:
      ~/.ollama/models/blobs/sha256-<hash>
    and manifests under:
      ~/.ollama/models/manifests/registry.ollama.ai/library/<name>/<tag>
    We seed the blobs referenced by the manifest.
    """
    name, _, tag = model_id.partition(":")
    tag = tag or "latest"
    manifest_path = (
        _OLLAMA_MODELS_DIR / "manifests" / "registry.ollama.ai" / "library" / name / tag
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    import json

    manifest = json.loads(manifest_path.read_text())
    blobs = []
    for layer in manifest.get("layers", []):
        digest = layer["digest"].replace(":", "-")  # sha256:abc → sha256-abc
        blob = _OLLAMA_MODELS_DIR / "blobs" / digest
        if blob.exists():
            blobs.append(blob)
    # also include the config blob
    cfg_digest = manifest.get("config", {}).get("digest", "").replace(":", "-")
    cfg_blob = _OLLAMA_MODELS_DIR / "blobs" / cfg_digest
    if cfg_blob.exists():
        blobs.append(cfg_blob)
    return blobs


def create_torrent(model_id: str) -> tuple[Path, str]:
    """Create a .torrent file for the model. Returns (torrent_path, magnet_uri)."""
    _TORRENTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = model_id.replace(":", "-").replace("/", "-")
    torrent_path = _TORRENTS_DIR / f"{safe_name}.torrent"

    if torrent_path.exists():
        log.info("Torrent already exists for %s", model_id)
        info = lt.torrent_info(str(torrent_path))
        magnet = lt.make_magnet_uri(info)
        return torrent_path, magnet

    blobs = _blob_paths_for_model(model_id)
    if not blobs:
        raise RuntimeError(f"No blobs found for model {model_id}")

    log.info("Creating torrent for %s (%d blob(s))", model_id, len(blobs))

    fs = lt.file_storage()
    # Add all blobs under a named folder so they unpack cleanly
    folder = safe_name
    for blob in blobs:
        lt.add_files(fs, str(blob))

    ct = lt.create_torrent(fs)
    ct.set_comment(f"AIDA OS model: {model_id}")
    ct.set_creator("AIDA OS seeder")
    # Use DHT only — no central tracker
    ct.add_node(("router.bittorrent.com", 6881))
    ct.add_node(("dht.transmissionbt.com", 6881))

    lt.set_piece_hashes(ct, str(blobs[0].parent))

    torrent_data = lt.bencode(ct.generate())
    torrent_path.write_bytes(torrent_data)

    info = lt.torrent_info(str(torrent_path))
    magnet = lt.make_magnet_uri(info)
    log.info("Torrent created: %s", magnet)
    return torrent_path, magnet


def _update_torrent_registry(model_id: str, magnet: str) -> None:
    import yaml

    registry: dict = {}
    if _TORRENT_REGISTRY.exists():
        registry = yaml.safe_load(_TORRENT_REGISTRY.read_text()) or {}
    registry.setdefault("magnets", {})[model_id] = magnet
    _TORRENT_REGISTRY.write_text(yaml.dump(registry, default_flow_style=False))


class ModelSeeder:
    """Manages a libtorrent session that seeds all pulled models."""

    def __init__(self, listen_port: int = 6881) -> None:
        self._session = lt.session()
        self._session.listen_on(listen_port, listen_port + 10)
        self._session.add_dht_router("router.bittorrent.com", 6881)
        self._session.add_dht_router("dht.transmissionbt.com", 6881)
        self._session.start_dht()
        self._handles: dict[str, lt.torrent_handle] = {}
        log.info("Seeder session started on port %d", listen_port)

    def seed(self, model_id: str) -> str:
        """Create torrent (if needed) and start seeding. Returns magnet URI."""
        torrent_path, magnet = create_torrent(model_id)
        _update_torrent_registry(model_id, magnet)

        if model_id not in self._handles:
            params = lt.add_torrent_params()
            params.ti = lt.torrent_info(str(torrent_path))
            params.save_path = str(_OLLAMA_MODELS_DIR / "blobs")
            handle = self._session.add_torrent(params)
            self._handles[model_id] = handle
            log.info("Seeding %s", model_id)
        return magnet

    def download(self, magnet: str, save_path: Path | None = None) -> lt.torrent_handle:
        """Add a magnet link for download + seeding."""
        dest = save_path or (_OLLAMA_MODELS_DIR / "blobs")
        dest.mkdir(parents=True, exist_ok=True)
        params = lt.parse_magnet_uri(magnet)
        params.save_path = str(dest)
        handle = self._session.add_torrent(params)
        log.info("Downloading via torrent: %s", magnet)
        return handle

    async def wait_for_download(
        self, handle: lt.torrent_handle, poll_interval: float = 2.0
    ) -> None:
        """Async wait until a torrent finishes downloading."""
        while not handle.is_seed():
            s = handle.status()
            log.info(
                "Downloading %.1f%% — peers: %d — %.1f kB/s",
                s.progress * 100,
                s.num_peers,
                s.download_rate / 1024,
            )
            await asyncio.sleep(poll_interval)
        log.info("Download complete, now seeding")

    def stats(self) -> list[dict]:
        out = []
        for model_id, handle in self._handles.items():
            s = handle.status()
            out.append(
                {
                    "model": model_id,
                    "seeding": handle.is_seed(),
                    "peers": s.num_peers,
                    "upload_rate_kbps": round(s.upload_rate / 1024, 1),
                    "total_uploaded_mb": round(s.total_upload / (1024 * 1024), 1),
                }
            )
        return out
