"""Tests for the iblai tauri command group."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from iblai_cli.cli import cli
from iblai_cli.commands.tauri import _detect_exec_prefix


class TestTauriCommandGroup:
    """Test the iblai tauri CLI help and structure."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_tauri_command_in_main_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "tauri" in result.output

    def test_tauri_help_shows_passthrough_docs(self, runner):
        result = runner.invoke(cli, ["tauri"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "ci-workflow" in result.output
        assert "pnpm exec tauri" in result.output

    def test_tauri_init_help(self, runner):
        result = runner.invoke(cli, ["tauri", "init", "--help"])
        assert result.exit_code == 0
        assert "Add Tauri" in result.output

    def test_tauri_ci_workflow_help(self, runner):
        result = runner.invoke(cli, ["tauri", "ci-workflow", "--help"])
        assert result.exit_code == 0
        assert "--desktop" in result.output
        assert "--ios" in result.output
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

    @patch("iblai_cli.commands.tauri._has_rust", return_value=False)
    def test_passthrough_missing_rust_exits(self, mock_rust, runner):
        """Passing unknown args to tauri checks for Rust first."""
        result = runner.invoke(cli, ["tauri", "dev"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "Rust toolchain not found" in result.output or "rustup" in result.output

    @patch("iblai_cli.commands.tauri._has_rust", return_value=True)
    @patch("iblai_cli.commands.tauri.subprocess.run")
    def test_passthrough_missing_tauri_cli_exits(self, mock_run, mock_rust, runner):
        """If @tauri-apps/cli is not installed, print helpful message."""
        mock_run.return_value = type("R", (), {"returncode": 1})()
        result = runner.invoke(cli, ["tauri", "dev"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "@tauri-apps/cli not found" in result.output


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
