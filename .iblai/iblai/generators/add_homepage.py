"""Generator for replacing the default Next.js home page with ibl.ai branding."""

from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader

from iblai.project_detector import ProjectInfo


class AddHomepageGenerator:
    """Replaces the home page with an ibl.ai branded landing page."""

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

    def _find_home_page(self) -> Optional[Path]:
        """Find the home page in the app directory."""
        for candidate in [
            self.project.app_dir / "page.tsx",
            self.project.app_dir / "page.jsx",
            self.project.root / "app" / "page.tsx",
            self.project.root / "app" / "page.jsx",
        ]:
            if candidate.exists():
                return candidate
        return None

    def generate(self) -> List[str]:
        """Replace the home page. Returns list of affected file paths."""
        created: List[str] = []

        home_page = self._find_home_page()
        if not home_page:
            return created

        template = self.env.get_template("add/auth/home-page.tsx.j2")
        self._write(home_page, template.render({}))
        created.append(str(home_page.relative_to(self.project.root)))

        return created
