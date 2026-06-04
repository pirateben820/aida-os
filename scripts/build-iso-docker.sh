#!/usr/bin/env bash
# Build the AIDA OS ISO using Docker — no Arch Linux install needed.
# Works on Windows (WSL2 or Git Bash), macOS, and Linux.
#
# Requirements:
#   - Docker Desktop installed and running
#   - ~2 GB free disk space for the build
#
# Output: dist/aida-os-alpha.iso
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"

mkdir -p "$DIST_DIR"

echo "==> Building AIDA OS ISO inside Docker (archlinux image ~170 MB)"
echo "    Output: $DIST_DIR/aida-os-alpha.iso"
echo ""

docker run --rm --privileged \
    -v "$PROJECT_ROOT:/aida-os" \
    -v "$DIST_DIR:/dist" \
    archlinux:latest \
    bash -c '
        set -euo pipefail

        echo "--- Updating pacman keyring ---"
        pacman-key --init
        pacman-key --populate archlinux
        pacman -Sy --noconfirm archiso

        echo "--- Embedding AIDA OS source into airootfs ---"
        mkdir -p /aida-os/archiso/airootfs/opt/aida-os
        cp -r /aida-os/. /aida-os/archiso/airootfs/opt/aida-os/
        # remove noise from embedded copy
        rm -rf \
            /aida-os/archiso/airootfs/opt/aida-os/.git \
            /aida-os/archiso/airootfs/opt/aida-os/__pycache__ \
            /aida-os/archiso/airootfs/opt/aida-os/.venv \
            /aida-os/archiso/airootfs/opt/aida-os/dist

        echo "--- Running mkarchiso ---"
        mkarchiso -v -w /tmp/aida-work -o /dist /aida-os/archiso

        echo "--- Renaming output ---"
        iso=$(ls /dist/*.iso | head -1)
        mv "$iso" /dist/aida-os-alpha.iso

        echo "Done."
    '

echo ""
echo "ISO ready: $DIST_DIR/aida-os-alpha.iso"
ls -lh "$DIST_DIR/aida-os-alpha.iso"
echo ""
echo "Boot it in VirtualBox / QEMU / VMware."
echo "Minimum VM: 4 vCPUs, 8 GB RAM, 20 GB disk."
