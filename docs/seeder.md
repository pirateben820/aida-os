# Seeder — P2P Model Distribution

## What it does
After Ollama pulls a model, the seeder creates a `.torrent` from the model blobs
and seeds it via DHT (no central tracker). Other AIDA OS nodes download via torrent
instead of Ollama's servers — faster for everyone after the first install.

## Library
`python-libtorrent` (libtorrent 2.x) — installed via `pacman -S python-libtorrent`.
On non-Arch systems: `pip install libtorrent`

## Ollama model storage layout
```
~/.ollama/models/
  manifests/registry.ollama.ai/library/<name>/<tag>   ← JSON manifest
  blobs/sha256-<hash>                                   ← actual model data
```
The seeder reads the manifest to find which blobs to include in the torrent.

## Torrent storage
`.torrent` files: `~/.aida/torrents/<model-name>.torrent`
Magnet links registry: `config/model_torrents.yaml`

## DHT bootstrap nodes
`router.bittorrent.com:6881` and `dht.transmissionbt.com:6881`
No private tracker needed.

## API
```python
from seeder.seeder import ModelSeeder
s = ModelSeeder()
magnet = s.seed("qwen2.5-coder:7b")   # create torrent + start seeding
handle = s.download(magnet)            # download from peers
await s.wait_for_download(handle)      # async wait
s.stats()                              # list seeding status
```

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `libtorrent` import error | Not installed | `pacman -S python-libtorrent` |
| `Manifest not found` | Model not pulled via Ollama | `ollama pull <model>` first |
| No peers found | First node on network | Normal — falls back to Ollama download |
| Seeder disabled warning | Import failed silently | Check libtorrent install |
