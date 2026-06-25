# PLABS Desktop - Proxmox Setup

## Order of operations

### Step 1 — Back up the Dell (DO THIS FIRST)
On the Dell (Windows 10), run as Administrator:
```
powershell -ExecutionPolicy Bypass -File backup.ps1
```
This copies everything to the SATA SSD. **Do not touch the SATA SSD after this.**

### Step 2 — Build the auto-install ISO
On any Linux machine (or WSL):
```bash
apt install proxmox-auto-install-assistant
# Edit answer.toml — set root_password and verify NVMe filter
proxmox-auto-install-assistant prepare-iso proxmox-ve_9.2-1.iso \
  --fetch-from iso --answer-file answer.toml \
  --output proxmox-ve_9.2-plabs.iso
```
Copy `proxmox-ve_9.2-plabs.iso` to the Ventoy USB (D:\).

### Step 3 — Install Proxmox
- Boot Dell from Ventoy USB
- Pick `proxmox-ve_9.2-plabs.iso` from the menu
- Walk away — auto-installs to NVMe, leaves SATA SSD alone

### Step 4 — Post-install
SSH into Proxmox at 192.168.88.3:
```bash
bash post-install.sh
reboot
```

### Step 5 — Deploy all VMs with Ansible
From your laptop:
```bash
cd ansible
ansible-playbook -i inventory.yml site.yml
```

## GPU Switching
- Windows gaming VM running → both 3060s passed through to Windows
- Windows off → start AIDA OS VM → both 3060s passed through to AI
- Never run both at the same time
