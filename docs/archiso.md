# archiso — ISO build profile

## What it does
`archiso` is Arch Linux's official tool for building bootable ISO images.
We use it to produce `aida-os-alpha.iso`. It is run inside a Docker container
on GitHub Actions using the `archlinux:latest` image.

## Required files in `archiso/`

| File / Dir | Required | Purpose |
|---|---|---|
| `profiledef.sh` | yes | ISO metadata and boot mode list |
| `pacman.conf` | yes | Which repos to pull packages from during build |
| `packages.x86_64` | yes | Packages to include in the live image |
| `efiboot/loader/loader.conf` | yes (UEFI) | systemd-boot timeout and default entry |
| `efiboot/loader/entries/*.conf` | yes (UEFI) | Kernel + initramfs + cmdline for each boot entry |
| `airootfs/` | yes | Files copied verbatim into the live root filesystem |

## profiledef.sh — key fields

```bash
iso_label        # Must match archisolabel= in efiboot entry cmdline
install_dir      # Subdirectory on ISO — default "arch", must match boot entry paths
bootmodes        # See boot modes below
pacman_conf      # Path relative to profile dir — must exist
```

## Boot modes (archiso v88+)

**Use only these — old names cause validation errors:**

| Modern name | Old deprecated name |
|---|---|
| `uefi-x64.systemd-boot.esp` | same (still valid in v88) |
| `bios.syslinux` | `bios.syslinux.mbr` / `bios.syslinux.eltorito` |

**Alpha uses UEFI only** (`uefi-x64.systemd-boot.esp` + `uefi-x64.systemd-boot.eltorito`).
No BIOS/syslinux — not needed for VMs (VirtualBox/QEMU/VMware all support UEFI).

If you add `bios.syslinux` you also need:
- `syslinux` in `packages.x86_64`
- `archiso/syslinux/` directory with config files

## efiboot entry format

```
title   Display name shown in boot menu
linux   /arch/boot/x86_64/vmlinuz-linux
initrd  /arch/boot/x86_64/initramfs-linux.img
options archisobasedir=arch archisolabel=AIDA_OS_ALPHA quiet
```

`archisobasedir` must match `install_dir` in profiledef.sh.
`archisolabel` must match `iso_label` in profiledef.sh.

## pacman.conf minimum content

Must include `[core]` and `[extra]` with mirrorlist. No `[multilib]` needed for the live image.

## airootfs embedding (CI workflow)

The source tree gets copied into `airootfs/opt/aida-os/` so the installer can
copy it to disk. **Never `cp /src /src/sub/` — always stage to a temp dir first.**

```bash
cp -r /aida-os/. /tmp/aida-src/          # stage
cp -r /tmp/aida-src/. /aida-os/archiso/airootfs/opt/aida-os/   # embed
```

## Common failures and fixes

| Error | Cause | Fix |
|---|---|---|
| `pacman.conf does not exist` | Missing file | Add `archiso/pacman.conf` |
| `syslinux package missing` | BIOS boot mode listed but syslinux not in packages | Remove BIOS boot modes or add syslinux |
| `efiboot/loader/entries missing` | UEFI boot mode listed but no entries dir | Create `efiboot/loader/entries/` with at least one `.conf` |
| `cannot copy directory into itself` | `cp -r /src /src/sub/` | Stage to `/tmp` first |
| `deprecated boot mode warning` | Old mode name | Use names from the table above |
