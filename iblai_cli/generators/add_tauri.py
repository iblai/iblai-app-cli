"""Generator for adding Tauri v2 desktop shell to a Next.js project."""

import json
import re
from pathlib import Path
from typing import List

from rich.console import Console

from iblai_cli.generators.base import BaseGenerator
from iblai_cli.next_config_patcher import (
    find_next_config,
    patch_next_config_for_tauri,
)

console = Console()


class AddTauriGenerator:
    """Add Tauri v2 desktop shell to an existing Next.js project.

    Generates src-tauri/ with a minimal Tauri configuration, patches
    next.config.mjs to remove @tauri-apps/api stubs and add conditional
    static export for Tauri builds, and updates package.json with Tauri
    dependencies and scripts.
    """

    def __init__(self, project_root: str, app_name: str = ""):
        self.root = Path(project_root)
        self.app_name = app_name or self._detect_app_name()
        self._generator = BaseGenerator(
            app_name=self.app_name,
            platform_key="",
            output_dir=project_root,
        )

    def _detect_app_name(self) -> str:
        """Read the app name from package.json or use directory name."""
        pkg_path = self.root / "package.json"
        if pkg_path.exists():
            try:
                data = json.loads(pkg_path.read_text(encoding="utf-8"))
                return data.get("name", self.root.name)
            except (json.JSONDecodeError, KeyError):
                pass
        return self.root.name

    def generate(self) -> List[str]:
        """Generate Tauri files and patch the project. Returns list of created/modified files."""
        created = []

        # 1. Render src-tauri/ templates
        created.extend(self._generate_src_tauri())

        # 2. Patch next.config
        patched = patch_next_config_for_tauri(self.root)
        if patched:
            created.append(patched)

        # 3. Patch package.json
        pkg_patched = self._patch_package_json()
        if pkg_patched:
            created.append("package.json")

        return created

    def _generate_src_tauri(self) -> List[str]:
        """Render all src-tauri/ files from templates."""
        created = []
        context = {
            "app_name": self.app_name,
        }

        template_map = {
            "tauri/src-tauri/tauri.conf.json.j2": "src-tauri/tauri.conf.json",
            "tauri/src-tauri/Cargo.toml.j2": "src-tauri/Cargo.toml",
            "tauri/src-tauri/src/main.rs.j2": "src-tauri/src/main.rs",
            "tauri/src-tauri/src/lib.rs.j2": "src-tauri/src/lib.rs",
            "tauri/src-tauri/capabilities/default.json.j2": "src-tauri/capabilities/default.json",
            "tauri/src-tauri/AppxManifest.xml.j2": "src-tauri/AppxManifest.xml",
            "tauri/src-tauri/build-msix.ps1.j2": "src-tauri/build-msix.ps1",
        }

        for template_name, output_path in template_map.items():
            out = self.root / output_path
            out.parent.mkdir(parents=True, exist_ok=True)
            content = self._generator.render_template(template_name, **context)
            out.write_text(content, encoding="utf-8")
            created.append(output_path)

        # Static files (not templates)
        build_rs = self.root / "src-tauri" / "build.rs"
        build_rs.write_text(
            "fn main() {\n    tauri_build::build()\n}\n", encoding="utf-8"
        )
        created.append("src-tauri/build.rs")

        return created

    def _patch_package_json(self) -> bool:
        """Add Tauri deps and scripts to package.json. Returns True if modified."""
        pkg_path = self.root / "package.json"
        if not pkg_path.exists():
            return False

        content = pkg_path.read_text(encoding="utf-8")
        data = json.loads(content)
        modified = False

        # Add dependencies
        deps = data.setdefault("dependencies", {})
        if "@tauri-apps/api" not in deps:
            deps["@tauri-apps/api"] = "^2.9.1"
            modified = True

        # Add devDependencies
        dev_deps = data.setdefault("devDependencies", {})
        if "@tauri-apps/cli" not in dev_deps:
            dev_deps["@tauri-apps/cli"] = "^2.5.0"
            modified = True

        # Add scripts
        scripts = data.setdefault("scripts", {})
        tauri_scripts = {
            "tauri:dev": "tauri dev",
            "tauri:build": "tauri build",
            "tauri:build:debug": "next build && tauri build --debug",
            "tauri:build:msix": "pwsh src-tauri/build-msix.ps1",
            "tauri:build:msix:arm64": "pwsh src-tauri/build-msix.ps1 -Architecture arm64",
        }
        for key, val in tauri_scripts.items():
            if key not in scripts:
                scripts[key] = val
                modified = True

        if modified:
            pkg_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        return modified

    def generate_ci_workflows(
        self,
        desktop: bool = True,
        ios: bool = False,
        windows_msix: bool = False,
    ) -> List[str]:
        """Generate GitHub Actions workflow files for Tauri builds."""
        created = []
        context = {"app_name": self.app_name}
        workflows_dir = self.root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        if desktop:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-desktop.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-desktop.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-desktop.yml")

        if ios:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-ios.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-ios.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-ios.yml")

        if windows_msix:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-windows-msix.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-windows-msix.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-windows-msix.yml")

        return created
