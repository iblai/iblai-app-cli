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
pip install . -q

# ---- PyInstaller ----
Write-Host "==> Building binary with PyInstaller..."
pyinstaller `
  --onefile `
  --name iblai `
  --add-data "iblai_cli/templates;iblai_cli/templates" `
  --hidden-import=iblai_cli `
  --hidden-import=iblai_cli.config `
  --hidden-import=iblai_cli.commands `
  --hidden-import=iblai_cli.commands.startapp `
  --hidden-import=iblai_cli.commands.add `
  --hidden-import=iblai_cli.commands.tauri `
  --hidden-import=iblai_cli.generators `
  --hidden-import=iblai_cli.generators.base `
  --hidden-import=iblai_cli.generators.base_app `
  --hidden-import=iblai_cli.generators.agent `
  --hidden-import=iblai_cli.generators.add_auth `
  --hidden-import=iblai_cli.generators.add_chat `
  --hidden-import=iblai_cli.generators.add_profile `
  --hidden-import=iblai_cli.generators.add_notifications `
  --hidden-import=iblai_cli.generators.add_mcp `
  --hidden-import=iblai_cli.generators.add_tauri `
  --hidden-import=iblai_cli.ai_helper `
  --hidden-import=iblai_cli.project_detector `
  --hidden-import=iblai_cli.package_manager `
  --hidden-import=iblai_cli.next_config_patcher `
  --copy-metadata readchar `
  --copy-metadata rich `
  --copy-metadata inquirer `
  iblai_cli/cli.py

# ---- Verify ----
Write-Host "==> Verifying binary..."
./dist/iblai.exe --version

Write-Host ""
Write-Host "Binary built: $((Get-Item dist/iblai.exe).FullName)"
Write-Host "Size: $([math]::Round((Get-Item dist/iblai.exe).Length / 1MB, 1)) MB"
