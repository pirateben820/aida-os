#!/bin/bash
# PLABS — One command to build the entire stack
# Run this after Proxmox installs:
#   curl -fsSL https://raw.githubusercontent.com/pirateben820/aida-os/main/proxmox/setup.sh | bash

set -e
echo "======================================"
echo "  PLABS Stack — One-Shot Setup"
echo "======================================"

# Install Ansible + Git
apt-get update -qq
apt-get install -y -qq git ansible python3-pip
pip3 install proxmoxer -q

# Clone the repo
git clone https://github.com/pirateben820/aida-os.git /opt/plabs-setup
cd /opt/plabs-setup

# Detect GPU PCI IDs and inject into vars
GPU0=$(lspci | grep -i nvidia | grep -iv audio | awk 'NR==1{print $1}')
GPU1=$(lspci | grep -i nvidia | grep -iv audio | awk 'NR==2{print $1}')
echo "gpu_pci_0: \"$GPU0\"" >> ansible/vars.yml
echo "gpu_pci_1: \"$GPU1\"" >> ansible/vars.yml

echo "Detected GPUs: $GPU0 and $GPU1"
echo ""
echo "Starting Ansible — this will configure the host,"
echo "create all VMs, and set up every service."
echo ""

# Run the full playbook
ansible-playbook -i ansible/inventory.yml ansible/site.yml -e @ansible/vars.yml

echo ""
echo "======================================"
echo "  DONE. Your stack is ready:"
echo "  Proxmox:   https://192.168.88.3:8006"
echo "  Gitea:     http://192.168.88.11:3000"
echo "  AI API:    http://192.168.88.10:4000"
echo "  Portainer: http://192.168.88.11:9000"
echo "  TrueNAS:   http://192.168.88.13"
echo "======================================"
