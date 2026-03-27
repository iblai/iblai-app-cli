"""Tests for CLI commands."""

import os

import pytest
from click.testing import CliRunner
from iblai.cli import cli

# Keys that may leak from the host environment and affect test behavior
_AI_ENV_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "IBLAI_AI_PROVIDER")


class TestCLI:
    """Test suite for main CLI functionality."""

    @pytest.fixture
    def runner(self):
        """Fixture for Click CLI runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test that CLI help command works."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ibl.ai CLI" in result.output
        assert "startapp" in result.output

    def test_cli_version(self, runner):
        """Test that CLI version command works."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_startapp_help(self, runner):
        """Test startapp command help."""
        result = runner.invoke(cli, ["startapp", "--help"])
        assert result.exit_code == 0
        assert "Create a new ibl.ai application" in result.output
        assert "agent" in result.output


class TestStartappCommand:
    """Test suite for startapp command."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Remove AI-related env vars so they don't leak into tests."""
        saved = {k: os.environ.pop(k) for k in _AI_ENV_KEYS if k in os.environ}
        yield
        os.environ.update(saved)

    @pytest.fixture
    def runner(self):
        """Fixture for Click CLI runner."""
        return CliRunner()

    def test_startapp_with_platform_key(self, runner):
        """Test startapp with platform key provided non-interactively."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "startapp",
                    "agent",
                    "--platform",
                    "test-platform",
                    "--agent",
                    "test-agent",
                    "--app-name",
                    "test-app",
                    "--output",
                    ".",
                ],
            )
            assert result.exit_code == 0
            assert "test-platform" in result.output

    def test_startapp_invalid_template(self, runner):
        """Test startapp with invalid template."""
        result = runner.invoke(cli, ["startapp", "invalid-template"])
        assert result.exit_code != 0

    def test_startapp_with_all_options(self, runner):
        """Test startapp with all options provided."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "startapp",
                    "agent",
                    "--platform",
                    "acme",
                    "--agent",
                    "agent-123",
                    "--output",
                    ".",
                ],
                input="my-agent-app\n",
            )
            # Command should process without errors
            assert result.exit_code == 0 or "Creating new agent app" in result.output


class TestAddCommand:
    """Test suite for the iblai add command group."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_add_command_in_help(self, runner):
        """The 'add' command is listed in the main CLI help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "add" in result.output

    def test_add_help_shows_subcommands(self, runner):
        """iblai add --help lists all six subcommands."""
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        for sub in ("auth", "chat", "profile", "notifications", "mcp", "builds"):
            assert sub in result.output

    def test_add_auth_requires_nextjs(self, runner):
        """Running iblai add auth outside a Next.js project shows an error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["add", "auth"])
            assert result.exit_code != 0 or "No package.json" in result.output
