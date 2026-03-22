"""Generator for adding MCP config and Claude skills to an existing project."""

import json
from pathlib import Path
import shutil

from iblai_cli.project_detector import ProjectInfo


# .mcp.json content
MCP_CONFIG = {
    "mcpServers": {
        "iblai-js-mcp": {
            "command": "npx",
            "args": ["@iblai/mcp"],
        }
    }
}


class AddMcpGenerator:
    """Generates .mcp.json and Claude skill files for an existing project."""

    def __init__(self, project: ProjectInfo):
        self.project = project
        self.skills_source_dir = Path(__file__).parent.parent / "templates" / "skills"

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate(self) -> list[str]:
        """Generate MCP config and Claude skills. Returns list of created file paths."""
        created: list[str] = []

        # 1. .mcp.json
        mcp_path = self.project.root / ".mcp.json"
        self._write(mcp_path, json.dumps(MCP_CONFIG, indent=2) + "\n")
        created.append(".mcp.json")

        # 2. Claude skills
        skills_dest = self.project.root / ".claude" / "skills"
        if self.skills_source_dir.is_dir():
            for skill_file in sorted(self.skills_source_dir.glob("*.md")):
                dest = skills_dest / skill_file.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(skill_file, dest)
                created.append(str(dest.relative_to(self.project.root)))

        return created
