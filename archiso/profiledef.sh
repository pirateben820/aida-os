#!/usr/bin/env bash
# archiso profile for AIDA OS alpha
# Build with: mkarchiso -v -w /tmp/aida-work -o /tmp/aida-out .

iso_name="aida-os"
iso_label="AIDA_OS_ALPHA"
iso_publisher="AIDA OS Project"
iso_application="AIDA OS Alpha"
iso_version="0.1.0-alpha"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/usr/local/bin/aida-install"]="0:0:755"
  ["/usr/local/bin/aida-setup"]="0:0:755"
)
