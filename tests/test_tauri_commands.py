"""Tests for the iblai tauri command group."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from iblai_cli.cli import cli


class TestTauriCommandGroup:
    """Test the iblai tauri CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_tauri_command_in_main_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "tauri" in result.output

    def test_tauri_help_shows_subcommands(self, runner):
        result = runner.invoke(cli, ["tauri", "--help"])
        assert result.exit_code == 0
        for sub in ("init", "dev", "build", "icon", "ios", "android", "ci-workflow"):
            assert sub in result.output

    def test_tauri_ios_help_shows_subcommands(self, runner):
        result = runner.invoke(cli, ["tauri", "ios", "--help"])
        assert result.exit_code == 0
        for sub in ("init", "dev", "build"):
            assert sub in result.output

    def test_tauri_android_help_shows_subcommands(self, runner):
        result = runner.invoke(cli, ["tauri", "android", "--help"])
        assert result.exit_code == 0
        for sub in ("init", "dev", "build"):
            assert sub in result.output


class TestTauriPrerequisites:
    """Test prerequisite checking logic."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("iblai_cli.commands.tauri.shutil.which", return_value=None)
    def test_dev_missing_rust_exits(self, mock_which, runner):
        result = runner.invoke(cli, ["tauri", "dev"])
        assert result.exit_code != 0
        assert "Rust toolchain not found" in result.output or "rustup" in result.output

    @patch("iblai_cli.commands.tauri._has_rust", return_value=True)
    @patch("iblai_cli.commands.tauri._has_tauri_cli", return_value=True)
    def test_dev_missing_src_tauri_exits(self, mock_cli, mock_rust, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["tauri", "dev"])
            assert result.exit_code != 0
            assert "src-tauri" in result.output

    @patch("iblai_cli.commands.tauri.platform.system", return_value="Linux")
    def test_ios_on_linux_exits(self, mock_system, runner):
        result = runner.invoke(cli, ["tauri", "ios", "init"])
        assert result.exit_code != 0
        assert "macOS" in result.output


class TestTauriInit:
    """Test iblai tauri init command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_init_requires_package_json(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["tauri", "init"])
            assert result.exit_code != 0
            assert "package.json" in result.output

    def test_init_creates_src_tauri(self, runner, tmp_path):
        import json
        import os

        pkg = {"name": "test-app", "version": "0.1.0"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "next.config.mjs").write_text(
            "const nextConfig = {};\nexport default nextConfig;\n"
        )
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(cli, ["tauri", "init"])
            assert result.exit_code == 0
            assert (tmp_path / "src-tauri").is_dir()
            assert (tmp_path / "src-tauri" / "tauri.conf.json").exists()
        finally:
            os.chdir(original_dir)

    def test_init_skips_if_exists(self, runner, tmp_path):
        import json
        import os

        pkg = {"name": "test-app", "version": "0.1.0"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "src-tauri").mkdir()
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(cli, ["tauri", "init"])
            assert result.exit_code == 0
            assert "already exists" in result.output
        finally:
            os.chdir(original_dir)
