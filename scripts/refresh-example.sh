#!/usr/bin/env bash
# Regenerate the example app at examples/iblai-agent-app/.
# Run this after making changes to generators or templates.
#
# Usage:
#   ./scripts/refresh-example.sh
#   make example
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

EXAMPLE_DIR="$ROOT_DIR/examples/iblai-agent-app"

# Clean previous generation
if [ -d "$EXAMPLE_DIR" ]; then
  echo "==> Removing old example..."
  rm -rf "$EXAMPLE_DIR"
fi

echo "==> Generating example agent app with Tauri..."
cd "$ROOT_DIR"

python3 -c "
from iblai.generators.agent import AgentAppGenerator
from iblai.generators.add_tauri import AddTauriGenerator

gen = AgentAppGenerator(
    app_name='iblai-agent-app',
    platform_key='iblai',
    mentor_id='00000000-0000-0000-0000-000000000000',
    output_dir='examples/iblai-agent-app',
    tauri=True,
)
gen.generate()

tauri_gen = AddTauriGenerator(
    project_root='examples/iblai-agent-app',
    app_name='iblai-agent-app',
)
tauri_gen.generate()

print('Done.')
"

FILE_COUNT=$(find "$EXAMPLE_DIR" -type f | wc -l | tr -d ' ')
echo ""
echo "Example app generated at: $EXAMPLE_DIR"
echo "Files: $FILE_COUNT"
