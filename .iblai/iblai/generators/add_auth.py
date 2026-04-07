"""Generator for adding ibl.ai auth to an existing Next.js project."""

import json
import os
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from iblai.next_config_patcher import (
    patch_globals_css,
    patch_next_config,
    write_env_local,
)
from iblai.package_manager import install_dev_packages, install_packages
from iblai.project_detector import ProjectInfo

# Dependencies required for auth integration.
AUTH_DEPS = [
    "@iblai/iblai-js",
    "@reduxjs/toolkit",
    "react-redux",
    "sonner",
    "lucide-react",
    "tw-animate-css",
    "@tauri-apps/api",
]

# Dev dependencies for SDK component styling + testing.
AUTH_DEV_DEPS = [
    "tailwind-scrollbar",
    "vitest",
    "@playwright/test",
    "cross-env",
    "dotenv",
]

# Default env vars for .env.local.
# Values are read from os.environ (set by config.load_config / DOMAIN shorthand)
# with iblai.app fallbacks.
_DEFAULT_ENV_VARS = {
    "NEXT_PUBLIC_API_BASE_URL": "https://api.iblai.app",
    "NEXT_PUBLIC_AUTH_URL": "https://login.iblai.app",
    "NEXT_PUBLIC_BASE_WS_URL": "wss://asgi.data.iblai.app",
    "NEXT_PUBLIC_PLATFORM_BASE_DOMAIN": "iblai.app",
}


def _auth_env_vars() -> dict:
    """Build env vars dict from os.environ with iblai.app defaults."""
    env = {k: os.environ.get(k, v) for k, v in _DEFAULT_ENV_VARS.items()}
    token = os.environ.get("IBLAI_API_KEY")
    if token:
        env["IBLAI_API_KEY"] = token
    return env


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

    def generate(self) -> List[str]:
        """Generate all auth files and apply project-level patches.

        Returns list of created/patched file paths (relative to project root).
        """
        created: List[str] = []

        # 1. SSO callback page
        sso_path = self.project.app_dir / "sso-login-complete" / "page.tsx"
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

        # 7b. Tenant resolution helper
        tenant_path = self.project.lib_dir / "iblai" / "tenant.ts"
        self._write(tenant_path, self._render("add/auth/tenant.ts.j2"))
        created.append(str(tenant_path.relative_to(self.project.root)))

        # 8. Patch next.config.{ts,mjs,js} (localStorage polyfill + RTK dedup)
        config_file = patch_next_config(self.project.root)
        created.append(f"{config_file} (patched)")

        # 9. Patch globals.css (add @import for iblai-styles.css)
        css_file = patch_globals_css(self.project.root, self.project.app_dir)
        if css_file:
            created.append(f"{css_file} (patched)")

        # 10. Write .env.local
        env_vars = {**_auth_env_vars(), "NEXT_PUBLIC_MAIN_TENANT_KEY": self.platform_key}
        write_env_local(self.project.root, env_vars)
        created.append(".env.local")

        # 11. Install dependencies
        install_packages(self.project.root, AUTH_DEPS)
        install_dev_packages(self.project.root, AUTH_DEV_DEPS)

        # 12. Create SDK symlink: lib/iblai/sdk -> node_modules/@iblai/iblai-js/dist
        #     This provides a stable path for the @source directive in iblai-styles.css
        #     to scan SDK compiled JS for Tailwind class generation.
        sdk_link = self.project.lib_dir / "iblai" / "sdk"
        if not sdk_link.exists():
            target = self.project.root / "node_modules" / "@iblai" / "iblai-js" / "dist"
            rel_target = os.path.relpath(target, sdk_link.parent)
            sdk_link.symlink_to(rel_target)
        created.append(
            f"{sdk_link.relative_to(self.project.root)} -> "
            "node_modules/@iblai/iblai-js/dist (symlink)"
        )

        # 13. Generate vitest config + source path test (if not already present)
        vitest_config = self.project.root / "vitest.config.ts"
        if not vitest_config.exists():
            self._write(
                vitest_config,
                self.env.get_template("shared/vitest.config.ts.j2").render({}),
            )
            created.append("vitest.config.ts")

        test_file = self.project.root / "__tests__" / "source-paths.test.ts"
        if not test_file.exists():
            self._write(
                test_file,
                self.env.get_template(
                    "shared/__tests__/source-paths.test.ts.j2"
                ).render({}),
            )
            created.append("__tests__/source-paths.test.ts")

        # 14. Generate Playwright e2e tests
        created.extend(self._generate_e2e())

        # 15. Patch package.json with e2e scripts
        if self._patch_e2e_scripts():
            created.append("package.json (e2e scripts)")

        return created

    def _generate_e2e(self) -> List[str]:
        """Generate Playwright e2e test files in e2e/."""
        created: List[str] = []
        e2e_dir = self.project.root / "e2e"

        e2e_files = {
            "shared/e2e/playwright.config.ts.j2": "e2e/playwright.config.ts",
            "shared/e2e/auth.setup.ts.j2": "e2e/auth.setup.ts",
            "shared/e2e/.env.development.j2": "e2e/.env.development",
            "shared/e2e/journeys/auth.journey.spec.ts.j2": "e2e/journeys/auth.journey.spec.ts",
        }

        for template_path, output_path in e2e_files.items():
            dest = self.project.root / output_path
            if not dest.exists():
                self._write(dest, self._render(template_path))
                created.append(output_path)

        return created

    def _patch_e2e_scripts(self) -> bool:
        """Add e2e test scripts to package.json. Returns True if modified."""
        pkg_path = self.project.root / "package.json"
        if not pkg_path.exists():
            return False

        data = json.loads(pkg_path.read_text(encoding="utf-8"))
        scripts = data.setdefault("scripts", {})
        modified = False

        e2e_scripts = {
            "test:e2e": "playwright test --config e2e/playwright.config.ts",
            "test:e2e:ui": "playwright test --config e2e/playwright.config.ts --ui",
            "test:e2e:headed": "cross-env HEADED=true playwright test --config e2e/playwright.config.ts",
        }

        for key, val in e2e_scripts.items():
            if key not in scripts:
                scripts[key] = val
                modified = True

        if modified:
            pkg_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        return modified
