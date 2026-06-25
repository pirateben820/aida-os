#!/bin/bash
# PLABS — Master Setup Script
# Run this ONE command after Proxmox is installed:
#   curl -fsSL https://raw.githubusercontent.com/pirateben/aida-os/main/proxmox/setup.sh | bash
#
# What it does:
#   1. Configures Proxmox host (IOMMU, NVIDIA passthrough, repos)
#   2. Reboots
#   3. On next boot — creates all VMs and runs Ansible on each
#   4. You walk away and come back to a full stack

set -e
REPO="https://raw.githubusercontent.com/pirateben/aida-os/main"
WORK="/opt/plabs-setup"

echo "======================================"
echo "  PLABS Stack — One-Shot Setup"
echo "======================================"

mkdir -p "$WORK"
cd "$WORK"

# --- Step 1: Clone the repo ---
apt-get install -y -qq git ansible python3
git clone https://github.com/pirateben/aida-os.git . 2>/dev/null || git pull

# --- Step 2: Run post-install (IOMMU, VFIO, repos, NVIDIA blacklist) ---
bash proxmox/post-install.sh

# --- Step 3: Install first-boot service that creates VMs after reboot ---
cat > /etc/systemd/system/plabs-firstboot.service << 'EOF'
[Unit]
Description=PLABS First Boot VM Setup
After=network-online.target pve-manager.service
Wants=network-online.target
ConditionPathExists=/opt/plabs-setup/proxmox/firstboot.sh

[Service]
Type=oneshot
ExecStart=/bin/bash /opt/plabs-setup/proxmox/firstboot.sh
ExecStartPost=/bin/systemctl disable plabs-firstboot.service
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl enable plabs-firstboot.service

echo ""
echo "======================================"
echo "  Rebooting in 10 seconds..."
echo "  After reboot, VMs will be created"
echo "  automatically. Check progress at:"
echo "  https://$(hostname -I | awk '{print $1}'):8006"
echo "======================================"
sleep 10
reboot
