"""Tests for npx/uvx/pipx distribution infrastructure."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Repo root for the feat-install branch
REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# PyInstaller _MEIPASS template resolution
# ---------------------------------------------------------------------------


class TestMeipassTemplateResolution:
    """BaseGenerator.template_dir respects sys._MEIPASS for frozen binaries."""

    def test_template_dir_uses_meipass_when_frozen(self, tmp_path):
        fake_meipass = str(tmp_path / "meipass")
        (tmp_path / "meipass" / "iblai_cli" / "templates").mkdir(parents=True)
        with patch.object(sys, "_MEIPASS", fake_meipass, create=True):
            from iblai_cli.generators.agent import AgentAppGenerator

            gen = AgentAppGenerator(
                app_name="t", platform_key="p", output_dir=str(tmp_path / "out")
            )
            assert gen.template_dir == Path(fake_meipass) / "iblai_cli" / "templates"

    def test_template_dir_uses_source_when_not_frozen(self, tmp_path):
        # Ensure _MEIPASS is absent
        with patch.object(sys, "_MEIPASS", None, create=True):
            from iblai_cli.generators.agent import AgentAppGenerator

            gen = AgentAppGenerator(
                app_name="t", platform_key="p", output_dir=str(tmp_path / "out")
            )
            expected = Path(__file__).parent.parent / "iblai_cli" / "templates"
            assert gen.template_dir == expected


# ---------------------------------------------------------------------------
# npm wrapper (iblai.js)
# ---------------------------------------------------------------------------


class TestNpmWrapper:
    """Validate the Node.js launcher script."""

    def test_iblai_js_has_correct_shebang(self):
        js_path = REPO_ROOT / "npm" / "cli" / "bin" / "iblai.js"
        first_line = js_path.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env node"

    def test_iblai_js_platforms_match_optional_deps(self):
        """The PLATFORMS object in iblai.js must align with package.json optionalDependencies."""
        js_text = (REPO_ROOT / "npm" / "cli" / "bin" / "iblai.js").read_text()
        pkg = json.loads((REPO_ROOT / "npm" / "cli" / "package.json").read_text())

        opt_deps = set(pkg.get("optionalDependencies", {}).keys())
        # Extract platform keys from the JS source: lines like "  'linux-x64': {"
        import re

        js_platforms = set(re.findall(r'"([a-z0-9]+-[a-z0-9]+)":\s*\{', js_text))
        # Map JS platform keys to npm package names
        js_pkg_names = {f"@iblai/cli-{p}" for p in js_platforms}
        assert js_pkg_names == opt_deps, (
            f"Mismatch: JS has {js_pkg_names}, package.json has {opt_deps}"
        )


# ---------------------------------------------------------------------------
# npm platform packages
# ---------------------------------------------------------------------------

PLATFORM_DIRS = [
    "cli-linux-x64",
    "cli-linux-arm64",
    "cli-darwin-arm64",
    "cli-win32-x64",
]

EXPECTED_OS_CPU = {
    "cli-linux-x64": (["linux"], ["x64"]),
    "cli-linux-arm64": (["linux"], ["arm64"]),
    "cli-darwin-arm64": (["darwin"], ["arm64"]),
    "cli-win32-x64": (["win32"], ["x64"]),
}


class TestNpmPlatformPackages:
    """Validate all platform-specific npm packages."""

    @pytest.mark.parametrize("platform_dir", PLATFORM_DIRS)
    def test_platform_package_has_valid_json(self, platform_dir):
        pkg_path = REPO_ROOT / "npm" / platform_dir / "package.json"
        pkg = json.loads(pkg_path.read_text())
        for field in ("name", "version", "os", "cpu", "files", "publishConfig"):
            assert field in pkg, f"{platform_dir}/package.json missing '{field}'"

    @pytest.mark.parametrize("platform_dir", PLATFORM_DIRS)
    def test_platform_package_os_cpu_correct(self, platform_dir):
        pkg = json.loads(
            (REPO_ROOT / "npm" / platform_dir / "package.json").read_text()
        )
        expected_os, expected_cpu = EXPECTED_OS_CPU[platform_dir]
        assert pkg["os"] == expected_os
        assert pkg["cpu"] == expected_cpu

    def test_platform_package_versions_match_main(self):
        main_pkg = json.loads((REPO_ROOT / "npm" / "cli" / "package.json").read_text())
        main_version = main_pkg["version"]
        for platform_dir in PLATFORM_DIRS:
            pkg = json.loads(
                (REPO_ROOT / "npm" / platform_dir / "package.json").read_text()
            )
            assert pkg["version"] == main_version, (
                f"{platform_dir} version {pkg['version']} != main {main_version}"
            )

    def test_main_cli_package_has_bin_entry(self):
        pkg = json.loads((REPO_ROOT / "npm" / "cli" / "package.json").read_text())
        assert "bin" in pkg
        assert "iblai" in pkg["bin"]
        assert pkg["bin"]["iblai"] == "bin/iblai.js"

    @pytest.mark.parametrize("platform_dir", PLATFORM_DIRS)
    def test_platform_bin_gitkeep_exists(self, platform_dir):
        gitkeep = REPO_ROOT / "npm" / platform_dir / "bin" / ".gitkeep"
        assert gitkeep.exists(), f"{platform_dir}/bin/.gitkeep missing"


# ---------------------------------------------------------------------------
# pyproject.toml
# ---------------------------------------------------------------------------


class TestPyprojectDistribution:
    """Validate pyproject.toml distribution settings."""

    @pytest.fixture(autouse=True)
    def _load_pyproject(self):
        # Use tomllib (3.11+) or tomli as fallback
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        self.pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    def test_dual_entry_points(self):
        scripts = self.pyproject["project"]["scripts"]
        assert "iblai" in scripts
        assert "iblai-app-cli" in scripts
        assert scripts["iblai"] == scripts["iblai-app-cli"]

    def test_pyinstaller_in_dev_deps(self):
        dev_deps = self.pyproject["project"]["optional-dependencies"]["dev"]
        assert any("pyinstaller" in d for d in dev_deps)


# ---------------------------------------------------------------------------
# GitHub Actions workflows
# ---------------------------------------------------------------------------


class TestGitHubWorkflows:
    """Validate CI/CD workflow structure."""

    def _load_yaml(self, name: str) -> dict:
        path = REPO_ROOT / ".github" / "workflows" / name
        return yaml.safe_load(path.read_text())

    def test_build_binaries_covers_all_platforms(self):
        wf = self._load_yaml("build-binaries.yml")
        targets = {
            m["target"] for m in wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        }
        expected = {
            "linux-x64",
            "linux-arm64",
            "darwin-arm64",
            "win32-x64",
        }
        assert targets == expected

    def test_build_binaries_includes_template_data(self):
        text = (REPO_ROOT / ".github" / "workflows" / "build-binaries.yml").read_text()
        assert "--add-data" in text
        assert "iblai_cli/templates" in text

    def test_publish_npm_downloads_all_artifacts(self):
        text = (REPO_ROOT / ".github" / "workflows" / "publish-npm.yml").read_text()
        for platform_dir in PLATFORM_DIRS:
            target = platform_dir.replace("cli-", "")
            assert f"iblai-{target}" in text, f"Missing download for {target}"

    def test_publish_pypi_workflow_exists(self):
        path = REPO_ROOT / ".github" / "workflows" / "publish-pypi.yml"
        assert path.exists()


# ---------------------------------------------------------------------------
# .gitignore
# ---------------------------------------------------------------------------


class TestGitignore:
    """Validate .gitignore has distribution-related entries."""

    def test_gitignore_excludes_platform_binaries(self):
        gitignore = (REPO_ROOT / ".gitignore").read_text()
        assert "node_modules/" in gitignore
        assert "*.spec" in gitignore
        for platform_dir in PLATFORM_DIRS:
            # e.g., npm/cli-linux-x64/bin/iblai
            assert platform_dir in gitignore
