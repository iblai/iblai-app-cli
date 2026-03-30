"""Tests for the iblai builds command group."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from iblai.cli import cli
from iblai.commands.builds import _detect_exec_prefix


class TestTauriCommandGroup:
    """Test the iblai builds CLI help and structure."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_tauri_command_in_main_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "builds" in result.output

    def test_tauri_help_shows_passthrough_docs(self, runner):
        result = runner.invoke(cli, ["builds"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "generate-icons" in result.output
        assert "ci-workflow" in result.output
        assert "devices" in result.output
        assert "screenshots" in result.output
        assert "pnpm exec tauri" in result.output

    def test_devices_help(self, runner):
        result = runner.invoke(cli, ["builds", "devices", "--help"])
        assert result.exit_code == 0
        assert (
            "simulators" in result.output.lower()
            or "emulators" in result.output.lower()
        )

    def test_screenshots_help(self, runner):
        result = runner.invoke(cli, ["builds", "screenshots", "--help"])
        assert result.exit_code == 0
        assert "--pages" in result.output
        assert "--url" in result.output
        assert "Playwright" in result.output

    def test_screenshots_generates_file(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["builds", "screenshots"])
            assert result.exit_code == 0
            assert Path("e2e/screenshots.spec.ts").exists()
            content = Path("e2e/screenshots.spec.ts").read_text()
            assert "test.describe" in content
            assert "Apple Watch" in content
            assert "iPhone" in content
            assert "localhost:3000" in content

    def test_screenshots_custom_pages(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["builds", "screenshots", "--pages", "/", "--pages", "/profile"]
            )
            assert result.exit_code == 0
            content = Path("e2e/screenshots.spec.ts").read_text()
            assert '"home"' in content
            assert '"profile"' in content

    def test_tauri_generate_icons_help(self, runner):
        result = runner.invoke(cli, ["builds", "generate-icons", "--help"])
        assert result.exit_code == 0
        assert "ImageMagick" in result.output
        assert "source" in result.output.lower()

    def test_tauri_init_help(self, runner):
        result = runner.invoke(cli, ["builds", "init", "--help"])
        assert result.exit_code == 0
        assert "Add Tauri" in result.output

    def test_tauri_ci_workflow_help(self, runner):
        result = runner.invoke(cli, ["builds", "ci-workflow", "--help"])
        assert result.exit_code == 0
        assert "--desktop" in result.output
        assert "--ios" in result.output
        assert "--windows-msix" in result.output
        assert "--all" in result.output


class TestExecPrefixDetection:
    """Test package manager detection for tauri exec prefix."""

    def test_pnpm_lockfile(self, tmp_path):
        (tmp_path / "pnpm-lock.yaml").touch()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert _detect_exec_prefix() == ["pnpm", "exec"]
        finally:
            os.chdir(original)

    def test_bun_lockfile(self, tmp_path):
        (tmp_path / "bun.lock").touch()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert _detect_exec_prefix() == ["bunx"]
        finally:
            os.chdir(original)

    def test_bun_lockb(self, tmp_path):
        (tmp_path / "bun.lockb").touch()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert _detect_exec_prefix() == ["bunx"]
        finally:
            os.chdir(original)

    def test_fallback_npx(self, tmp_path):
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert _detect_exec_prefix() == ["npx"]
        finally:
            os.chdir(original)

    def test_pnpm_takes_priority_over_bun(self, tmp_path):
        (tmp_path / "pnpm-lock.yaml").touch()
        (tmp_path / "bun.lock").touch()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert _detect_exec_prefix() == ["pnpm", "exec"]
        finally:
            os.chdir(original)


class TestTauriPrerequisites:
    """Test prerequisite checking logic."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("iblai.commands.builds._has_rust", return_value=False)
    def test_passthrough_missing_rust_exits(self, mock_rust, runner):
        """Passing unknown args to tauri checks for Rust first."""
        result = runner.invoke(cli, ["builds", "dev"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "Rust toolchain not found" in result.output or "rustup" in result.output

    @patch("iblai.commands.builds._has_rust", return_value=True)
    @patch("iblai.commands.builds.subprocess.run")
    def test_passthrough_missing_tauri_cli_exits(self, mock_run, mock_rust, runner):
        """If @tauri-apps/cli is not installed, print helpful message."""
        mock_run.return_value = type("R", (), {"returncode": 1})()
        result = runner.invoke(cli, ["builds", "dev"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "@tauri-apps/cli not found" in result.output


class TestTauriInit:
    """Test iblai builds init command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_init_requires_package_json(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["builds", "init"])
            assert result.exit_code != 0
            assert "package.json" in result.output

    def test_init_creates_src_tauri(self, runner, tmp_path):
        pkg = {"name": "test-app", "version": "0.1.0"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "next.config.ts").write_text(
            "const nextConfig = {};\nexport default nextConfig;\n"
        )
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(cli, ["builds", "init"])
            assert result.exit_code == 0
            assert (tmp_path / "src-tauri").is_dir()
            assert (tmp_path / "src-tauri" / "tauri.conf.json").exists()
        finally:
            os.chdir(original_dir)

    def test_init_skips_if_exists(self, runner, tmp_path):
        pkg = {"name": "test-app", "version": "0.1.0"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "src-tauri").mkdir()
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(cli, ["builds", "init"])
            assert result.exit_code == 0
            assert "already exists" in result.output
        finally:
            os.chdir(original_dir)
