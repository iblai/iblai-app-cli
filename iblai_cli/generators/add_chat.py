"""Generator for adding IBL.ai chat widget to an existing Next.js project."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from iblai_cli.project_detector import ProjectInfo


class AddChatGenerator:
    """Generates a chat widget component for an existing project."""

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

    def generate(self) -> list[str]:
        """Generate the chat widget. Returns list of created file paths."""
        created: list[str] = []

        widget_path = self.project.components_dir / "iblai" / "chat-widget.tsx"
        self._write(widget_path, self._render("add/chat/chat-widget.tsx.j2"))
        created.append(str(widget_path.relative_to(self.project.root)))

        return created
