"""Generator for the 'base' template — minimal Next.js app with IBL.ai auth."""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from iblai_cli.generators.base import BaseGenerator


class BaseAppGenerator(BaseGenerator):
    """
    Generate a minimal Next.js app with IBL.ai authentication.

    This is a "blank canvas" with SSO auth, Redux store, and providers
    but no chat UI, sidebar, or agent-specific routes. Developers build
    their own pages and use ``iblai add`` to integrate features.
    """

    # Files that the AI ``--prompt`` enhancement may modify.
    ENHANCEABLE_FILES = [
        "app/globals.css",
        "app/(app)/page.tsx",
    ]

    def __init__(
        self,
        app_name: str,
        platform_key: str,
        output_dir: str,
        **kwargs: Any,
    ):
        super().__init__(
            app_name=app_name,
            platform_key=platform_key,
            output_dir=output_dir,
            **kwargs,
        )
        # Jinja2 loader: base-specific templates first, shared fallback
        self.env = Environment(
            loader=FileSystemLoader(
                [
                    str(self.template_dir / "base"),
                    str(self.template_dir / "shared"),
                    str(self.template_dir / "add"),
                ]
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_context(self) -> Dict[str, Any]:
        """Template context — no mentor_id for the base template."""
        return {
            "app_name": self.app_name,
            "platform_key": self.platform_key,
        }

    def _render(self, template_path: str) -> str:
        return self.env.get_template(template_path).render(self.get_context())

    def _write(self, rel_path: str, content: str) -> None:
        path = self.output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _copy_static(self, template_path: str, output_rel: str) -> None:
        """Copy a non-template file from the template dirs."""
        for search_dir in (self.template_dir / "base", self.template_dir / "shared"):
            src = search_dir / template_path
            if src.exists():
                dest = self.output_dir / output_rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                return

    def generate(self) -> None:
        """Generate the full base app."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # --- Project config (from shared + base) ---
        self._write("package.json", self._render("package.json.j2"))
        self._write("tsconfig.json", self._render("tsconfig.json.j2"))
        self._copy_static("declarations.d.ts", "declarations.d.ts")
        self._write("next.config.mjs", self._render("next.config.mjs.j2"))
        self._write("tailwind.config.ts", self._render("tailwind.config.ts.j2"))
        self._write("postcss.config.mjs", self._render("postcss.config.mjs.j2"))
        self._write(".env.example", self._render(".env.example.j2"))
        self._write(".gitignore", self._render(".gitignore.j2"))
        self._write(".eslintrc.json", self._render(".eslintrc.json.j2"))
        self._write(".mcp.json", self._render(".mcp.json.j2"))
        self._write("components.json", self._render("components.json.j2"))

        # --- Root layout + globals (from shared) ---
        self._write("app/layout.tsx", self._render("app/layout.tsx.j2"))
        self._copy_static("app/globals.css", "app/globals.css")

        # --- Route groups ---
        # (auth) — SSO callback, NO providers
        self._write(
            "app/(auth)/sso-login-complete/page.tsx",
            self._render("app/(auth)/sso-login-complete/page.tsx.j2"),
        )
        # (app) — authenticated, wrapped by AppShell
        self._write("app/(app)/layout.tsx", self._render("app/(app)/layout.tsx.j2"))
        self._write("app/(app)/page.tsx", self._render("app/(app)/page.tsx.j2"))

        # --- Components ---
        self._write(
            "components/app-shell.tsx", self._render("components/app-shell.tsx.j2")
        )
        self._write(
            "components/ui/button.tsx", self._render("components/ui/button.tsx.j2")
        )
        self._write(
            "components/ui/sonner.tsx", self._render("components/ui/sonner.tsx.j2")
        )

        # --- IBL.ai components (pre-generated, ready to import) ---
        self._write(
            "components/iblai/chat-widget.tsx",
            self._render("chat/chat-widget.tsx.j2"),
        )
        self._write(
            "components/iblai/profile-dropdown.tsx",
            self._render("profile/profile-dropdown.tsx.j2"),  # exports ProfileDropdown
        )
        self._write(
            "components/iblai/notification-bell.tsx",
            self._render("notifications/notification-bell.tsx.j2"),
        )

        # --- Providers + Store ---
        self._write("providers/index.tsx", self._render("providers/index.tsx.j2"))
        self._write(
            "providers/store-provider.tsx",
            self._render("providers/store-provider.tsx.j2"),
        )
        self._write("store/index.ts", self._render("store/index.ts.j2"))

        # --- Lib ---
        self._write("lib/config.ts", self._render("lib/config.ts.j2"))
        self._write("lib/utils.ts", self._render("lib/utils.ts.j2"))
        self._write("lib/hooks.ts", self._render("lib/hooks.ts.j2"))

        # --- Lib shims for `iblai add` compatibility ---
        # Components added via `iblai add chat/profile` import from
        # "@/lib/iblai/config" and "@/lib/iblai/auth-utils". These re-export
        # shims ensure those imports resolve to the base template's files.
        self._write("lib/iblai/config.ts", self._render("lib/iblai/config.ts.j2"))
        self._write(
            "lib/iblai/auth-utils.ts", self._render("lib/iblai/auth-utils.ts.j2")
        )

        # --- Hooks ---
        self._write("hooks/use-user.ts", self._render("hooks/use-user.ts.j2"))

        # --- Public ---
        self._write("public/env.js", self._render("public/env.js.j2"))
        self._write("public/README.md", self._render("public/README.md.j2"))

        # --- Claude skills (.claude/skills/) — copy all files (md + images) ---
        import shutil

        skills_src = self.template_dir / "skills"
        if skills_src.is_dir():
            for skill_file in sorted(skills_src.iterdir()):
                if skill_file.is_file():
                    dest = self.output_dir / ".claude" / "skills" / skill_file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_file, dest)

        # --- OpenCode skills (.opencode/skills/<name>/) — copy all files ---
        opencode_src = self.template_dir / "opencode-skills"
        if opencode_src.is_dir():
            for skill_dir in sorted(opencode_src.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    for skill_file in sorted(skill_dir.iterdir()):
                        if skill_file.is_file():
                            dest = (
                                self.output_dir
                                / ".opencode"
                                / "skills"
                                / skill_dir.name
                                / skill_file.name
                            )
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(skill_file, dest)

        # --- Playwright E2E tests (e2e/ directory) ---
        self._write(
            "e2e/playwright.config.ts", self._render("e2e/playwright.config.ts.j2")
        )
        self._write("e2e/auth.setup.ts", self._render("e2e/auth.setup.ts.j2"))
        self._write("e2e/custom-reporter.ts", self._render("e2e/custom-reporter.ts.j2"))
        self._write("e2e/.env.development", self._render("e2e/.env.development.j2"))
        self._write(
            "e2e/journeys/auth.journey.spec.ts",
            self._render("e2e/journeys/auth.journey.spec.ts.j2"),
        )
        self._write(
            "e2e/journeys/chat.journey.spec.ts",
            self._render("e2e/journeys/chat.journey.spec.ts.j2"),
        )
