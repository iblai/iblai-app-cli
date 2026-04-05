"""Generator for adding MCP config and skills to an existing project."""

import json
import os
from pathlib import Path
import shutil
from typing import List

from iblai.package_manager import install_dev_packages
from iblai.project_detector import ProjectInfo


# .mcp.json content
MCP_CONFIG = {
    "mcpServers": {
        "iblai-js-mcp": {
            "command": "npx",
            "args": ["@iblai/mcp"],
        },
        "playwright": {
            "command": "npx",
            "args": ["@playwright/mcp@latest"],
        },
        "shadcn": {
            "command": "npx",
            "args": ["shadcn@latest", "mcp"],
        },
    }
}

# MCP dev dependency.
MCP_DEPS = ["@iblai/mcp"]


class AddMcpGenerator:
    """Generates .mcp.json and skills (Claude, OpenCode, Cursor) for an existing project."""

    def __init__(self, project: ProjectInfo):
        self.project = project
        self.skills_source_dir = Path(__file__).parent.parent / "templates" / "skills"
        self.screenshots_source_dir = (
            Path(__file__).parent.parent / "templates" / "screenshots"
        )

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate(self) -> List[str]:
        """Generate MCP config and skills. Returns list of created file paths."""
        created: List[str] = []

        # 1. .mcp.json
        mcp_path = self.project.root / ".mcp.json"
        self._write(mcp_path, json.dumps(MCP_CONFIG, indent=2) + "\n")
        created.append(".mcp.json")

        # 2. Skills — categorized source, symlinked flat to Claude/OpenCode/Cursor
        if self.skills_source_dir.is_dir():
            skills_dest = self.project.root / "skills"
            claude_dest = self.project.root / ".claude" / "skills"
            opencode_dest = self.project.root / ".opencode" / "skills"
            cursor_dest = self.project.root / ".cursor" / "rules"

            for d in (skills_dest, claude_dest, opencode_dest, cursor_dest):
                d.mkdir(parents=True, exist_ok=True)

            for skill_file in sorted(self.skills_source_dir.rglob("*.md")):
                # README.md goes to skills/ root only — no symlinks
                if skill_file.name == "README.md":
                    shutil.copy2(skill_file, skills_dest / "README.md")
                    created.append("skills/README.md")
                    continue

                # Relative path within skills/ (e.g., "components/iblai-add-auth.md")
                rel_path = skill_file.relative_to(self.skills_source_dir)
                parts = rel_path.parts

                # Copy actual file preserving subdirectory structure
                dest_file = skills_dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill_file, dest_file)
                created.append(f"skills/{rel_path}")

                # Only symlink top-level skill files (category/name.md),
                # not nested support files (category/references/foo.md)
                if len(parts) != 2:
                    continue

                skill_name = skill_file.stem

                # Symlink for Claude Code (flat)
                claude_link = claude_dest / skill_file.name
                if not claude_link.exists():
                    os.symlink(f"../../skills/{rel_path}", str(claude_link))

                # Symlink for OpenCode (directory per skill, flat)
                oc_dir = opencode_dest / skill_name
                oc_dir.mkdir(parents=True, exist_ok=True)
                oc_link = oc_dir / "SKILL.md"
                if not oc_link.exists():
                    os.symlink(f"../../../skills/{rel_path}", str(oc_link))

                # Symlink for Cursor (flat)
                cursor_link = cursor_dest / skill_file.name
                if not cursor_link.exists():
                    os.symlink(f"../../skills/{rel_path}", str(cursor_link))

            # Copy non-markdown support files (scripts, licenses, etc.)
            for support_file in sorted(self.skills_source_dir.rglob("*")):
                if support_file.is_dir() or support_file.suffix == ".md":
                    continue
                rel_path = support_file.relative_to(self.skills_source_dir)
                dest_file = skills_dest / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(support_file, dest_file)
                created.append(f"skills/{rel_path}")

        # 3. Screenshots (docs/screenshots/)
        if self.screenshots_source_dir.is_dir():
            screenshots_dest = self.project.root / "docs" / "screenshots"
            screenshots_dest.mkdir(parents=True, exist_ok=True)
            for img in sorted(self.screenshots_source_dir.iterdir()):
                if img.is_file():
                    shutil.copy2(img, screenshots_dest / img.name)

        # 4. Install @iblai/mcp as dev dependency
        install_dev_packages(self.project.root, MCP_DEPS)

        return created
