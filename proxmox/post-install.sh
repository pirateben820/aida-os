#!/bin/bash
# Proxmox Post-Install Script - plabs-desktop
# Dell Dual Xeon E5-2698 V4 / 128GB / 2x RTX 3060
# Run once after first boot: bash post-install.sh

set -e
echo "=== PLABS Proxmox Post-Install ==="

# --- SSH — lock it in first so we never lose remote access ---
systemctl enable ssh
systemctl start ssh
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh
echo "SSH enabled on port 22 — root login allowed"

# --- No-subscription repo ---
sed -i 's|^deb https://enterprise.proxmox.com|# deb https://enterprise.proxmox.com|g' /etc/apt/sources.list.d/pve-enterprise.list
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-no-sub.list
apt-get update -qq

# --- Intel IOMMU for GPU passthrough ---
GRUB_CFG="/etc/default/grub"
IOMMU_PARAMS="intel_iommu=on iommu=pt"
if ! grep -q "intel_iommu" "$GRUB_CFG"; then
    sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"quiet\"/GRUB_CMDLINE_LINUX_DEFAULT=\"quiet $IOMMU_PARAMS\"/" "$GRUB_CFG"
    update-grub
    echo "IOMMU enabled in GRUB"
fi

# --- VFIO modules for GPU passthrough ---
cat >> /etc/modules <<EOF
vfio
vfio_iommu_type1
vfio_pci
EOF

# Blacklist NVIDIA on host — GPUs belong to VMs, not the host
cat > /etc/modprobe.d/blacklist-nvidia.conf <<EOF
blacklist nouveau
blacklist nvidia
blacklist nvidiafb
options vfio-pci ids=10de:2504,10de:228b
EOF

update-initramfs -u -k all
echo "VFIO + GPU blacklist configured"

# --- NUMA tuning for dual Xeon ---
apt-get install -y -qq numactl numad
systemctl enable numad
echo "NUMA tuning enabled"

# --- Useful tools ---
apt-get install -y -qq \
    htop iotop nvme-cli pciutils lshw \
    ansible git curl wget

# --- Show GPU PCI IDs so user can verify ---
echo ""
echo "=== GPU PCI IDs (verify these match blacklist-nvidia.conf) ==="
lspci -nn | grep -i nvidia
echo ""
echo "=== IOMMU Groups (GPUs need their own group for passthrough) ==="
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=${d#*/iommu_groups/*}; n=${n%%/*}
    printf 'IOMMU Group %s ' "$n"
    lspci -nns "${d##*/}"
done | grep -i nvidia

echo ""
echo "=== Post-install done. Reboot to activate IOMMU + VFIO ==="
echo "After reboot, run: ansible-playbook ansible/site.yml"
