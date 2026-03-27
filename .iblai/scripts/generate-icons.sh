#!/usr/bin/env bash
# Regenerate Tauri template icons from docs/iblai-logo.png.
# Requires: ImageMagick v6 (convert command)
#
# Usage:
#   ./.iblai/scripts/generate-icons.sh
#   make -C .iblai icons
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

SRC="$ROOT_DIR/docs/iblai-logo.png"
DST="$ROOT_DIR/.iblai/iblai/templates/icons"

if ! command -v convert &>/dev/null; then
  echo "Error: ImageMagick (convert) not found."
  echo "Install: sudo apt install imagemagick  # or: brew install imagemagick"
  exit 1
fi

if [ ! -f "$SRC" ]; then
  echo "Error: Source image not found: $SRC"
  exit 1
fi

mkdir -p "$DST"

echo "==> Generating icons from $SRC..."

# Tauri bundle icons (from tauri.conf.json)
convert "$SRC" -gravity center -background transparent -extent 32x32 "$DST/32x32.png"
convert "$SRC" -gravity center -background transparent -extent 128x128 "$DST/128x128.png"
convert "$SRC" -gravity center -background transparent -extent 256x256 "$DST/128x128@2x.png"
convert "$SRC" -gravity center -background transparent -extent 256x256 "$DST/icon.png"

# MSIX icons (from AppxManifest.xml)
convert "$SRC" -gravity center -background transparent -extent 50x50 "$DST/StoreLogo.png"
convert "$SRC" -gravity center -background transparent -extent 44x44 "$DST/Square44x44Logo.png"
convert "$SRC" -gravity center -background transparent -extent 71x71 "$DST/Square71x71Logo.png"
convert "$SRC" -gravity center -background transparent -extent 150x150 "$DST/Square150x150Logo.png"
convert "$SRC" -gravity center -background transparent -extent 310x310 "$DST/Square310x310Logo.png"
convert "$SRC" -gravity center -background transparent -extent 310x150 "$DST/Wide310x150Logo.png"

# Windows ICO (multi-resolution: 16, 32, 48, 256)
convert "$SRC" -gravity center -background transparent \
  \( -clone 0 -extent 16x16 \) \
  \( -clone 0 -extent 32x32 \) \
  \( -clone 0 -extent 48x48 \) \
  \( -clone 0 -extent 256x256 \) \
  -delete 0 "$DST/icon.ico"

echo ""
echo "Icons generated in: $DST"
ls -la "$DST"
