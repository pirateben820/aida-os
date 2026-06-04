#!/usr/bin/env bash
# Bootstrap AIDA OS development environment on Arch Linux.
# Run as a normal user (not root). Uses sudo where needed.
set -euo pipefail

echo "==> Updating system packages"
sudo pacman -Syu --noconfirm

echo "==> Installing base dependencies"
sudo pacman -S --needed --noconfirm \
  python \
  python-pip \
  python-virtualenv \
  python-libtorrent \
  docker \
  docker-compose \
  git \
  curl

echo "==> Enabling Docker"
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo "==> Installing Ollama"
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama

echo "==> Pulling starter models (~6 GB total)"
# qwen2.5-coder:7b  4.7 GB  — coding + general tasks
ollama pull qwen2.5-coder:7b
# deepseek-r1:1.5b  1.1 GB  — fast reasoning / math
ollama pull deepseek-r1:1.5b
# nomic-embed-text  274 MB  — embeddings for Hermes memory
ollama pull nomic-embed-text

echo "==> Creating Python venv"
python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo "==> Starting NATS (Docker)"
docker compose -f docker-compose.dev.yml up -d

echo ""
echo "==> Running first-boot AI setup wizard"
python -m setup.wizard

echo ""
echo "Bootstrap complete."
echo "Start aidad: python -m aidad"
