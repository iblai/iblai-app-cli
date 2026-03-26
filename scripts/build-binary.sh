#!/usr/bin/env bash
# Build iblai CLI as a standalone binary using PyInstaller.
# Works on Linux and macOS.  For Windows, use build-binary.ps1.
#
# Usage:
#   ./scripts/build-binary.sh            # build for current platform
#   IBLAI_VENV=0 ./scripts/build-binary.sh  # skip venv creation (CI)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

USE_VENV="${IBLAI_VENV:-1}"

# ---- Virtual environment ----
if [ "$USE_VENV" = "1" ]; then
  if [ ! -d ".venv-build" ]; then
    echo "==> Creating build virtualenv..."
    python3 -m venv .venv-build
  fi
  # shellcheck disable=SC1091
  source .venv-build/bin/activate
fi

# ---- Dependencies ----
echo "==> Installing dependencies..."
python -m pip install --upgrade pip -q
pip install pyinstaller -q
pip install . -q

# ---- PyInstaller ----
echo "==> Building binary with PyInstaller..."
pyinstaller \
  --onefile \
  --name iblai \
  --add-data "iblai_cli/templates:iblai_cli/templates" \
  --hidden-import=iblai_cli \
  --hidden-import=iblai_cli.config \
  --hidden-import=iblai_cli.commands \
  --hidden-import=iblai_cli.commands.startapp \
  --hidden-import=iblai_cli.commands.add \
  --hidden-import=iblai_cli.commands.tauri \
  --hidden-import=iblai_cli.generators \
  --hidden-import=iblai_cli.generators.base \
  --hidden-import=iblai_cli.generators.base_app \
  --hidden-import=iblai_cli.generators.agent \
  --hidden-import=iblai_cli.generators.add_auth \
  --hidden-import=iblai_cli.generators.add_chat \
  --hidden-import=iblai_cli.generators.add_profile \
  --hidden-import=iblai_cli.generators.add_notifications \
  --hidden-import=iblai_cli.generators.add_mcp \
  --hidden-import=iblai_cli.generators.add_tauri \
  --hidden-import=iblai_cli.ai_helper \
  --hidden-import=iblai_cli.project_detector \
  --hidden-import=iblai_cli.package_manager \
  --hidden-import=iblai_cli.next_config_patcher \
  --copy-metadata readchar \
  --copy-metadata rich \
  --copy-metadata inquirer \
  iblai_cli/cli.py

# ---- Verify ----
echo "==> Verifying binary..."
./dist/iblai --version

echo ""
echo "Binary built: $(pwd)/dist/iblai"
echo "Size: $(du -h dist/iblai | cut -f1)"
