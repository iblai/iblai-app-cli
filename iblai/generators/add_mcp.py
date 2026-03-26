"""Generator for adding MCP config and Claude skills to an existing project."""

import json
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
        }
    }
}

# MCP dev dependency.
MCP_DEPS = ["@iblai/mcp"]


class AddMcpGenerator:
    """Generates .mcp.json, Claude skills, and OpenCode skills for an existing project."""

    def __init__(self, project: ProjectInfo):
        self.project = project
        self.skills_source_dir = Path(__file__).parent.parent / "templates" / "skills"
        self.opencode_skills_source_dir = (
            Path(__file__).parent.parent / "templates" / "opencode-skills"
        )

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate(self) -> List[str]:
        """Generate MCP config and Claude skills. Returns list of created file paths."""
        created: List[str] = []

        # 1. .mcp.json
        mcp_path = self.project.root / ".mcp.json"
        self._write(mcp_path, json.dumps(MCP_CONFIG, indent=2) + "\n")
        created.append(".mcp.json")

        # 2. Claude skills (.claude/skills/) — copy all files (md + images)
        skills_dest = self.project.root / ".claude" / "skills"
        if self.skills_source_dir.is_dir():
            for skill_file in sorted(self.skills_source_dir.iterdir()):
                if skill_file.is_file():
                    dest = skills_dest / skill_file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_file, dest)
                    if skill_file.suffix == ".md":
                        created.append(str(dest.relative_to(self.project.root)))

        # 3. OpenCode skills (.opencode/skills/<name>/) — copy all files
        opencode_dest = self.project.root / ".opencode" / "skills"
        if self.opencode_skills_source_dir.is_dir():
            for skill_dir in sorted(self.opencode_skills_source_dir.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    for skill_file in sorted(skill_dir.iterdir()):
                        if skill_file.is_file():
                            dest = opencode_dest / skill_dir.name / skill_file.name
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(skill_file, dest)
                            if skill_file.name == "SKILL.md":
                                created.append(str(dest.relative_to(self.project.root)))

        # 4. Install @iblai/mcp as dev dependency
        install_dev_packages(self.project.root, MCP_DEPS)

        return created
