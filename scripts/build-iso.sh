#!/usr/bin/env bash
# Build the AIDA OS alpha ISO.
# Must run on an Arch Linux machine with archiso installed.
# Output: /tmp/aida-out/aida-os-*.iso
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROFILE_DIR="$PROJECT_ROOT/archiso"
WORK_DIR="/tmp/aida-work"
OUT_DIR="/tmp/aida-out"

echo "==> Installing archiso"
sudo pacman -S --needed --noconfirm archiso

echo "==> Copying AIDA OS source into airootfs"
# Embed the whole project into the ISO so the installer can copy it to disk
sudo mkdir -p "$PROFILE_DIR/airootfs/opt/aida-os"
sudo cp -r "$PROJECT_ROOT/." "$PROFILE_DIR/airootfs/opt/aida-os/"
# Remove the work dir and git noise from the embedded copy
sudo rm -rf \
    "$PROFILE_DIR/airootfs/opt/aida-os/.git" \
    "$PROFILE_DIR/airootfs/opt/aida-os/__pycache__" \
    "$PROFILE_DIR/airootfs/opt/aida-os/.venv"

echo "==> Cleaning previous build artifacts"
sudo rm -rf "$WORK_DIR" "$OUT_DIR"
mkdir -p "$OUT_DIR"

echo "==> Building ISO (this takes a few minutes)"
sudo mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"

echo ""
echo "ISO built successfully:"
ls -lh "$OUT_DIR"/*.iso
echo ""
echo "Boot it in VirtualBox / QEMU / VMware."
echo "Minimum VM specs: 4 vCPUs, 8 GB RAM, 20 GB disk."
