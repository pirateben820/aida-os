#!/bin/bash
# PLABS First Boot — runs once after post-install reboot
# Creates all VMs in Proxmox then runs Ansible on each

set -e
LOG="/var/log/plabs-firstboot.log"
exec > >(tee -a "$LOG") 2>&1

WORK="/opt/plabs-setup"
STORAGE="local-lvm"
BRIDGE="vmbr0"

echo "[$(date)] Starting PLABS first boot VM creation..."

# --- Download Ubuntu + TrueNAS ISOs if not on USB ---
ISO_DIR="/var/lib/vz/template/iso"
mkdir -p "$ISO_DIR"

download_iso() {
    local name=$1 url=$2
    if [ ! -f "$ISO_DIR/$name" ]; then
        echo "Downloading $name..."
        wget -q --show-progress -O "$ISO_DIR/$name" "$url"
    fi
}

download_iso "truenas-25.10.1.iso" "https://download.truenas.com/TrueNAS-SCALE-Goldeye/25.10.1/TrueNAS-SCALE-25.10.1.iso"
download_iso "ubuntu-server.iso"   "https://releases.ubuntu.com/24.04/ubuntu-24.04.2-live-server-amd64.iso"

# --- Helper: create a VM ---
create_vm() {
    local vmid=$1 name=$2 cores=$3 mem=$4 disk=$5 iso=$6 ip=$7
    echo "Creating VM $vmid: $name..."
    qm create "$vmid" \
        --name "$name" \
        --cores "$cores" \
        --memory "$mem" \
        --net0 "virtio,bridge=$BRIDGE" \
        --scsi0 "$STORAGE:$disk" \
        --ide2 "$ISO_DIR/$iso,media=cdrom" \
        --boot "order=ide2;scsi0" \
        --ostype l26 \
        --machine q35 \
        --bios ovmf \
        --efidisk0 "$STORAGE:1" \
        --ipconfig0 "ip=$ip/24,gw=192.168.88.1" \
        --onboot 1
}

# VM IDs and specs
# 100 = TrueNAS  (storage first — everything else mounts it)
# 101 = AIDA OS  (AI inference)
# 102 = Docker OS (services)
# 103 = Dev OS   (user workstations)
# 104 = Windows  (gaming — manual install, just create the shell)

create_vm 100 "truenas"    4  8192   32  "truenas-25.10.1.iso" "192.168.88.13"
create_vm 101 "aida-os"   12 32768  100  "aida-os-alpha.iso"   "192.168.88.10"
create_vm 102 "docker-os"  8 16384  200  "ubuntu-server.iso"   "192.168.88.11"
create_vm 103 "dev-os"     8 16384  150  "ubuntu-server.iso"   "192.168.88.12"

# Windows Gaming VM — no auto-install, just the shell
echo "Creating Windows gaming VM shell (104)..."
qm create 104 \
    --name "windows-gaming" \
    --cores 16 \
    --memory 49152 \
    --net0 "virtio,bridge=$BRIDGE" \
    --scsi0 "$STORAGE:300" \
    --machine q35 \
    --bios ovmf \
    --efidisk0 "$STORAGE:1" \
    --ostype win11 \
    --onboot 0

# --- GPU Passthrough — find both RTX 3060s ---
echo "Configuring GPU passthrough..."
GPU_IDS=$(lspci -nn | grep -i "NVIDIA" | grep -v "Audio" | awk '{print $1}')
AUDIO_IDS=$(lspci -nn | grep -i "NVIDIA" | grep "Audio" | awk '{print $1}')

i=0
for gpu in $GPU_IDS; do
    if [ $i -eq 0 ]; then TARGET=101; else TARGET=104; fi  # GPU0→AIDA, GPU1→Windows default
    qm set $TARGET --hostpci$i "$gpu,pcie=1,x-vga=1"
    i=$((i+1))
done

# Add NVIDIA audio to same VMs
i=0
for audio in $AUDIO_IDS; do
    if [ $i -eq 0 ]; then TARGET=101; else TARGET=104; fi
    qm set $TARGET --hostpci$((i+2)) "$audio"
    i=$((i+1))
done

# --- Start TrueNAS first, wait for it ---
echo "Starting TrueNAS VM..."
qm start 100
echo "TrueNAS started — configure storage at http://192.168.88.13 then press Enter"
read -t 300 || true  # wait up to 5 min or continue

# --- Run Ansible on remaining VMs ---
echo "Running Ansible playbooks..."
cd "$WORK"
ansible-playbook -i ansible/inventory.yml ansible/site.yml -e @ansible/vars.yml

echo "[$(date)] PLABS first boot complete!"
echo ""
echo "Services:"
echo "  Proxmox:  https://192.168.88.3:8006"
echo "  Gitea:    http://192.168.88.11:3000"
echo "  Portainer: http://192.168.88.11:9000"
echo "  AI API:   http://192.168.88.10:4000"
echo "  TrueNAS:  http://192.168.88.13"
