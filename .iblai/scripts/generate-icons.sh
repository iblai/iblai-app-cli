#!/usr/bin/env bash
# Regenerate Tauri template icons from docs/iblai-logo.png.
# Requires: ImageMagick v6 (convert command)
#
# Uses -resize to downscale (preserving aspect ratio) then -extent
# to pad to exact dimensions with transparent background.
#
# Usage:
#   ./.iblai/scripts/generate-icons.sh
#   make -C .iblai icons
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

SRC="$ROOT_DIR/.iblai/docs/iblai-logo.png"
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
echo "    Source: $(file -b "$SRC")"

# Tauri bundle icons (from tauri.conf.json)
convert "$SRC" -resize 32x32 -gravity center -background transparent -extent 32x32 "$DST/32x32.png"
convert "$SRC" -resize 128x128 -gravity center -background transparent -extent 128x128 "$DST/128x128.png"
convert "$SRC" -resize 256x256 -gravity center -background transparent -extent 256x256 "$DST/128x128@2x.png"
convert "$SRC" -resize 256x256 -gravity center -background transparent -extent 256x256 "$DST/icon.png"

# MSIX icons (from AppxManifest.xml)
convert "$SRC" -resize 50x50 -gravity center -background transparent -extent 50x50 "$DST/StoreLogo.png"
convert "$SRC" -resize 44x44 -gravity center -background transparent -extent 44x44 "$DST/Square44x44Logo.png"
convert "$SRC" -resize 71x71 -gravity center -background transparent -extent 71x71 "$DST/Square71x71Logo.png"
convert "$SRC" -resize 150x150 -gravity center -background transparent -extent 150x150 "$DST/Square150x150Logo.png"
convert "$SRC" -resize 310x310 -gravity center -background transparent -extent 310x310 "$DST/Square310x310Logo.png"
convert "$SRC" -resize 310x150 -gravity center -background transparent -extent 310x150 "$DST/Wide310x150Logo.png"

# Windows ICO (multi-resolution: 16, 32, 48, 256)
convert "$SRC" \
  \( -clone 0 -resize 16x16 -gravity center -background transparent -extent 16x16 \) \
  \( -clone 0 -resize 32x32 -gravity center -background transparent -extent 32x32 \) \
  \( -clone 0 -resize 48x48 -gravity center -background transparent -extent 48x48 \) \
  \( -clone 0 -resize 256x256 -gravity center -background transparent -extent 256x256 \) \
  -delete 0 "$DST/icon.ico"

echo ""
echo "Icons generated in: $DST"
ls -la "$DST"
