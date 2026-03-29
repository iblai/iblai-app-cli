# Build iblai CLI as a standalone binary using PyInstaller (Windows).
# Usage:  pwsh scripts/build-binary.ps1
$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ROOT_DIR) { $ROOT_DIR = Split-Path -Parent $PSScriptRoot }
Set-Location $ROOT_DIR

# ---- Bake commit ID ----
$Commit = git rev-parse --short HEAD 2>$null
if (-not $Commit) { $Commit = "unknown" }
Write-Host "==> Baking commit ID: $Commit"
$initFile = Join-Path $ROOT_DIR ".iblai\iblai\__init__.py"
(Get-Content $initFile) -replace '__commit__ = ""', "__commit__ = `"$Commit`"" | Set-Content $initFile

# ---- Dependencies ----
Write-Host "==> Installing dependencies..."
python -m pip install --upgrade pip -q
pip install pyinstaller -q
pip install (Join-Path $ROOT_DIR ".iblai") -q

# ---- PyInstaller ----
Write-Host "==> Building binary with PyInstaller..."
pyinstaller `
  --onefile `
  --name iblai `
  --add-data ".iblai/iblai/templates;iblai/templates" `
  --hidden-import=iblai `
  --hidden-import=iblai.config `
  --hidden-import=iblai.commands `
  --hidden-import=iblai.commands.startapp `
  --hidden-import=iblai.commands.add `
  --hidden-import=iblai.commands.builds `
  --hidden-import=iblai.commands.config `
  --hidden-import=iblai.generators `
  --hidden-import=iblai.generators.base `
  --hidden-import=iblai.generators.base_app `
  --hidden-import=iblai.generators.agent `
  --hidden-import=iblai.generators.add_auth `
  --hidden-import=iblai.generators.add_chat `
  --hidden-import=iblai.generators.add_profile `
  --hidden-import=iblai.generators.add_notifications `
  --hidden-import=iblai.generators.add_mcp `
  --hidden-import=iblai.generators.add_builds `
  --hidden-import=iblai.generators.add_account `
  --hidden-import=iblai.generators.add_analytics `
  --hidden-import=iblai.ai_helper `
  --hidden-import=iblai.project_detector `
  --hidden-import=iblai.package_manager `
  --hidden-import=iblai.next_config_patcher `
  --copy-metadata readchar `
  --copy-metadata rich `
  --copy-metadata inquirer `
  .iblai/iblai/cli.py

# ---- Restore __init__.py ----
try { git checkout "$initFile" 2>$null } catch {
    (Get-Content $initFile) -replace "__commit__ = `"$Commit`"", '__commit__ = ""' | Set-Content $initFile
}

# ---- Verify ----
Write-Host "==> Verifying binary..."
./dist/iblai.exe --version

Write-Host ""
Write-Host "Binary built: $((Get-Item dist/iblai.exe).FullName)"
Write-Host "Size: $([math]::Round((Get-Item dist/iblai.exe).Length / 1MB, 1)) MB"
