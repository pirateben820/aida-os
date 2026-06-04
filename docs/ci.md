# CI — GitHub Actions ISO build

## Workflow file
`.github/workflows/build-iso.yml`

## What it does
1. Checks out the repo
2. Runs `archlinux:latest` Docker container with `--privileged` (required by mkarchiso)
3. Installs `archiso` via pacman inside the container
4. Stages the source tree to `/tmp/aida-src/` then copies into `airootfs/opt/aida-os/`
5. Runs `mkarchiso`
6. Uploads the ISO as a GitHub Actions artifact (30-day retention)
7. Creates a GitHub Release with the ISO attached (on `main` branch pushes)

## Triggers
- Push to `main`
- Manual trigger via `workflow_dispatch`

## Required GitHub token scopes
The `gh auth` token needs the `workflow` scope to push `.github/workflows/` files.
Re-auth with: `gh auth refresh --hostname github.com --scopes workflow`

## Common failures

| Error | Cause | Fix |
|---|---|---|
| `refusing to allow OAuth App to create workflow` | Token missing `workflow` scope | Re-auth with `--scopes workflow` |
| `cannot copy directory into itself` | src and dest overlap | Stage to `/tmp/aida-src` first (already fixed) |
| `pacman.conf does not exist` | Missing file in profile | See [archiso.md](archiso.md) |
| `efiboot/loader/entries missing` | Missing boot entry config | See [archiso.md](archiso.md) |
| Build exits in <30s | Validation error before mkarchiso runs | Check `--log-failed` output |

## Checking build status
```powershell
$env:PATH = "$env:PATH;C:\Program Files\GitHub CLI"
gh run list --repo pirateben820/aida-os --limit 3
gh run view <run-id> --repo pirateben820/aida-os --log-failed
```

## Downloading the ISO
```powershell
gh release list --repo pirateben820/aida-os
gh release download <tag> --repo pirateben820/aida-os --pattern "*.iso"
```
