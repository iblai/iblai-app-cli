# Build iblai CLI as a standalone binary using PyInstaller (Windows).
# Usage:  pwsh scripts/build-binary.ps1
$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ROOT_DIR) { $ROOT_DIR = Split-Path -Parent $PSScriptRoot }
Set-Location $ROOT_DIR

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
  --hidden-import=iblai.commands.tauri `
  --hidden-import=iblai.generators `
  --hidden-import=iblai.generators.base `
  --hidden-import=iblai.generators.base_app `
  --hidden-import=iblai.generators.agent `
  --hidden-import=iblai.generators.add_auth `
  --hidden-import=iblai.generators.add_chat `
  --hidden-import=iblai.generators.add_profile `
  --hidden-import=iblai.generators.add_notifications `
  --hidden-import=iblai.generators.add_mcp `
  --hidden-import=iblai.generators.add_tauri `
  --hidden-import=iblai.ai_helper `
  --hidden-import=iblai.project_detector `
  --hidden-import=iblai.package_manager `
  --hidden-import=iblai.next_config_patcher `
  --copy-metadata readchar `
  --copy-metadata rich `
  --copy-metadata inquirer `
  .iblai/iblai/cli.py

# ---- Verify ----
Write-Host "==> Verifying binary..."
./dist/iblai.exe --version

Write-Host ""
Write-Host "Binary built: $((Get-Item dist/iblai.exe).FullName)"
Write-Host "Size: $([math]::Round((Get-Item dist/iblai.exe).Length / 1MB, 1)) MB"
