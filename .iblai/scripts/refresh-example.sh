#!/usr/bin/env bash
# Regenerate the example app at examples/iblai-agent-app/.
# Also copies skills to root and creates all symlinks.
#
# Run this after making changes to generators or templates.
#
# Usage:
#   make -C .iblai example
#   bash .iblai/scripts/refresh-example.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

EXAMPLE_DIR="$ROOT_DIR/examples/iblai-agent-app"

# --- Step 1: Clean old example ---
if [ -d "$EXAMPLE_DIR" ]; then
  echo "==> Removing old example..."
  rm -rf "$EXAMPLE_DIR"
fi

# --- Step 2: Generate fresh example app ---
echo "==> Generating example agent app with builds support..."
cd "$ROOT_DIR"

python3 -c "
from iblai.generators.agent import AgentAppGenerator
from iblai.generators.add_builds import AddBuildsGenerator

gen = AgentAppGenerator(
    app_name='iblai-agent-app',
    platform_key='iblai',
    mentor_id='00000000-0000-0000-0000-000000000000',
    output_dir='examples/iblai-agent-app',
    builds=True,
)
gen.generate()

builds_gen = AddBuildsGenerator(
    project_root='examples/iblai-agent-app',
    app_name='iblai-agent-app',
)
builds_gen.generate()

print('Generated.')
"

# --- Step 3: Copy generated skills to root ---
echo "==> Copying skills to root..."
rm -rf "$ROOT_DIR/skills"
cp -r "$EXAMPLE_DIR/skills" "$ROOT_DIR/skills"

# --- Step 4: Replace example skills/ with symlink to root ---
echo "==> Symlinking example skills to root..."
rm -rf "$EXAMPLE_DIR/skills"
ln -s ../../skills "$EXAMPLE_DIR/skills"

# --- Step 5: Recreate root-level tool symlinks (app + CLI dev) ---
echo "==> Creating root tool symlinks..."
rm -rf "$ROOT_DIR/.claude/skills" "$ROOT_DIR/.opencode/skills" "$ROOT_DIR/.cursor/rules"
mkdir -p "$ROOT_DIR/.claude/skills" "$ROOT_DIR/.opencode/skills" "$ROOT_DIR/.cursor/rules"

# App skills (from root skills/)
for f in "$ROOT_DIR"/skills/{setup,components,builds,testing}/*.md; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  [ "$name" = "README.md" ] && continue
  stem="${name%.md}"
  category=$(basename "$(dirname "$f")")

  ln -s "../skills/$category/$name" "$ROOT_DIR/.claude/skills/$name"
  mkdir -p "$ROOT_DIR/.opencode/skills/$stem"
  ln -s "../../skills/$category/$name" "$ROOT_DIR/.opencode/skills/$stem/SKILL.md"
  ln -s "../skills/$category/$name" "$ROOT_DIR/.cursor/rules/$name"
done

# CLI dev skills (from .iblai/skills/)
for f in "$ROOT_DIR"/.iblai/skills/{commands,builds,internals}/*.md; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  [ "$name" = "README.md" ] && continue
  stem="${name%.md}"
  category=$(basename "$(dirname "$f")")

  ln -s "../.iblai/skills/$category/$name" "$ROOT_DIR/.claude/skills/$name"
  mkdir -p "$ROOT_DIR/.opencode/skills/$stem"
  ln -s "../../.iblai/skills/$category/$name" "$ROOT_DIR/.opencode/skills/$stem/SKILL.md"
  ln -s "../.iblai/skills/$category/$name" "$ROOT_DIR/.cursor/rules/$name"
done

# --- Summary ---
FILE_COUNT=$(find "$EXAMPLE_DIR" -type f -not -path '*/.git/*' | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$ROOT_DIR/skills" -name '*.md' -not -name 'README.md' | wc -l | tr -d ' ')
SYMLINK_COUNT=$(ls "$ROOT_DIR/.claude/skills/" | wc -l | tr -d ' ')

echo ""
echo "Example app: $EXAMPLE_DIR"
echo "Files: $FILE_COUNT"
echo "Skills at root: $SKILL_COUNT app skills"
echo "Symlinks in .claude/skills/: $SYMLINK_COUNT (app + CLI dev)"
