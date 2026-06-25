# PLABS-DESKTOP BACKUP SCRIPT
# Run this on the Dell (Windows 10) before wiping
# Copies code, projects, and AI models to the SATA SSD (D: or E:)
# Find which drive is the SATA SSD (not C: NVMe, not USB)

$SOURCE_DRIVE = "C:"
$BACKUP_DRIVE = $null

# Auto-detect the SATA SSD (largest non-C non-USB fixed drive)
foreach ($vol in (Get-Volume | Where-Object { $_.DriveLetter -and $_.DriveLetter -ne 'C' -and $_.DriveType -eq 'Fixed' })) {
    $BACKUP_DRIVE = "$($vol.DriveLetter):"
    break
}

if (-not $BACKUP_DRIVE) {
    Write-Host "ERROR: Could not find SATA SSD. Plug in external drive or check disk management." -ForegroundColor Red
    exit 1
}

$DEST = "$BACKUP_DRIVE\PLABS_BACKUP"
Write-Host "Backing up to: $DEST" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $DEST | Out-Null

# --- What to back up ---
$TARGETS = @(
    # User files
    "$SOURCE_DRIVE\Users\$env:USERNAME\Documents",
    "$SOURCE_DRIVE\Users\$env:USERNAME\Desktop",
    "$SOURCE_DRIVE\Users\$env:USERNAME\Downloads",
    # Code / projects
    "$SOURCE_DRIVE\Users\$env:USERNAME\Projects",
    "$SOURCE_DRIVE\Users\$env:USERNAME\dev",
    "$SOURCE_DRIVE\Users\$env:USERNAME\code",
    "$SOURCE_DRIVE\Projects",
    "$SOURCE_DRIVE\dev",
    "$SOURCE_DRIVE\code",
    # AI models (Ollama stores here by default)
    "$SOURCE_DRIVE\Users\$env:USERNAME\.ollama",
    "$SOURCE_DRIVE\Users\$env:USERNAME\AppData\Local\ollama",
    # Other common model locations
    "$SOURCE_DRIVE\models",
    "$SOURCE_DRIVE\AI",
    "$SOURCE_DRIVE\LLM"
)

$total = 0
foreach ($src in $TARGETS) {
    if (Test-Path $src) {
        $name = Split-Path $src -Leaf
        $dst  = "$DEST\$name"
        Write-Host "Copying: $src" -ForegroundColor Yellow
        robocopy $src $dst /E /MT:8 /R:2 /W:5 /NP /LOG+:"$DEST\backup.log" | Out-Null
        $size = (Get-ChildItem $dst -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1GB
        $total += $size
        Write-Host "  Done: $([math]::Round($size,2)) GB" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Backup complete. Total: $([math]::Round($total,2)) GB saved to $DEST" -ForegroundColor Cyan
Write-Host "Log: $DEST\backup.log"
Write-Host ""
Write-Host "NEXT: Wipe the NVMe and install Proxmox from USB."
Write-Host "      The SATA SSD ($BACKUP_DRIVE) stays untouched."
