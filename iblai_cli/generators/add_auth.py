"""Generator for adding IBL.ai auth to an existing Next.js project."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from iblai_cli.project_detector import ProjectInfo


class AddAuthGenerator:
    """Generates auth integration files for an existing Next.js project."""

    def __init__(self, project: ProjectInfo, platform_key: str):
        self.project = project
        self.platform_key = platform_key
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _context(self):
        return {"platform_key": self.platform_key}

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _render(self, template_path: str) -> str:
        return self.env.get_template(template_path).render(self._context())

    def generate(self) -> list[str]:
        """Generate all auth files. Returns list of created file paths."""
        created: list[str] = []

        # 1. SSO callback page
        sso_dir = self.project.app_dir / "sso-login-complete"
        sso_path = sso_dir / "page.tsx"
        self._write(sso_path, self._render("add/auth/sso-login-complete-page.tsx.j2"))
        created.append(str(sso_path.relative_to(self.project.root)))

        # 2. Config
        config_path = self.project.lib_dir / "iblai" / "config.ts"
        self._write(config_path, self._render("add/auth/config.ts.j2"))
        created.append(str(config_path.relative_to(self.project.root)))

        # 3. Storage service
        storage_path = self.project.lib_dir / "iblai" / "storage-service.ts"
        self._write(storage_path, self._render("add/auth/storage-service.ts.j2"))
        created.append(str(storage_path.relative_to(self.project.root)))

        # 4. Auth utils
        auth_path = self.project.lib_dir / "iblai" / "auth-utils.ts"
        self._write(auth_path, self._render("add/auth/auth-utils.ts.j2"))
        created.append(str(auth_path.relative_to(self.project.root)))

        # 5. Redux store
        store_path = self.project.store_dir / "iblai-store.ts"
        self._write(store_path, self._render("add/auth/iblai-store.ts.j2"))
        created.append(str(store_path.relative_to(self.project.root)))

        # 6. Providers
        providers_path = self.project.providers_dir / "iblai-providers.tsx"
        self._write(providers_path, self._render("add/auth/iblai-providers.tsx.j2"))
        created.append(str(providers_path.relative_to(self.project.root)))

        # 7. IBL styles (CSS imports for SDK components)
        styles_path = self.project.app_dir / "iblai-styles.css"
        self._write(styles_path, self._render("add/auth/iblai-styles.css.j2"))
        created.append(str(styles_path.relative_to(self.project.root)))

        return created
