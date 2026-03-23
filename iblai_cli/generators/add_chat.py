"""Generator for adding IBL.ai chat widget to an existing Next.js project."""

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from iblai_cli.package_manager import install_packages
from iblai_cli.project_detector import ProjectInfo

# The only dependency: the <mentor-ai> Web Component.
CHAT_DEPS = ["@iblai/iblai-web-mentor"]


class AddChatGenerator:
    """Generates a chat widget component that wraps the <mentor-ai> Web Component."""

    def __init__(self, project: ProjectInfo):
        self.project = project
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _render(self, template_path: str) -> str:
        return self.env.get_template(template_path).render({})

    def generate(self) -> List[str]:
        """Generate the chat widget wrapper and install @iblai/iblai-web-mentor.

        Returns list of created file paths.
        """
        created: List[str] = []

        # 1. Generate chat widget component
        widget_path = self.project.components_dir / "iblai" / "chat-widget.tsx"
        self._write(widget_path, self._render("add/chat/chat-widget.tsx.j2"))
        created.append(str(widget_path.relative_to(self.project.root)))

        # 2. Install @iblai/iblai-web-mentor
        install_packages(self.project.root, CHAT_DEPS)

        return created
