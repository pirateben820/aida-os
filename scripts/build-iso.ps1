# Build the AIDA OS ISO on Windows using Docker Desktop.
# Run from PowerShell: .\scripts\build-iso.ps1

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$DistDir = Join-Path $ProjectRoot "dist"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

Write-Host "==> Building AIDA OS ISO inside Docker" -ForegroundColor Cyan
Write-Host "    Arch Linux image: ~170 MB download (one time)"
Write-Host "    Output: $DistDir\aida-os-alpha.iso"
Write-Host ""

# Convert Windows paths to Docker-compatible paths
$ProjectMount = $ProjectRoot -replace '\\', '/' -replace '^([A-Z]):', '/$1'
$DistMount    = $DistDir     -replace '\\', '/' -replace '^([A-Z]):', '/$1'

docker run --rm --privileged `
    -v "${ProjectMount}:/aida-os" `
    -v "${DistMount}:/dist" `
    archlinux:latest `
    bash -c @'
        set -euo pipefail
        pacman-key --init
        pacman-key --populate archlinux
        pacman -Sy --noconfirm archiso

        mkdir -p /aida-os/archiso/airootfs/opt/aida-os
        cp -r /aida-os/. /aida-os/archiso/airootfs/opt/aida-os/
        rm -rf \
            /aida-os/archiso/airootfs/opt/aida-os/.git \
            /aida-os/archiso/airootfs/opt/aida-os/__pycache__ \
            /aida-os/archiso/airootfs/opt/aida-os/.venv \
            /aida-os/archiso/airootfs/opt/aida-os/dist

        mkarchiso -v -w /tmp/aida-work -o /dist /aida-os/archiso
        iso=$(ls /dist/*.iso | head -1)
        mv "$iso" /dist/aida-os-alpha.iso
        echo "Done."
'@

if ($LASTEXITCODE -eq 0) {
    $iso = Get-Item "$DistDir\aida-os-alpha.iso"
    Write-Host ""
    Write-Host "ISO ready: $($iso.FullName)" -ForegroundColor Green
    Write-Host "Size: $([math]::Round($iso.Length / 1MB)) MB"
    Write-Host ""
    Write-Host "Boot in VirtualBox / QEMU / VMware" -ForegroundColor Cyan
    Write-Host "Minimum VM: 4 vCPUs, 8 GB RAM, 20 GB disk"
} else {
    Write-Host "Build failed. Check output above." -ForegroundColor Red
    exit 1
}
