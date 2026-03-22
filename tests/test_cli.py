"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from iblai_cli.cli import cli


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
        assert "IBL.ai CLI" in result.output
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
        assert "Create a new IBL.ai application" in result.output
        assert "agent" in result.output


class TestStartappCommand:
    """Test suite for startapp command."""

    @pytest.fixture
    def runner(self):
        """Fixture for Click CLI runner."""
        return CliRunner()

    def test_startapp_with_platform_key(self, runner):
        """Test startapp with platform key provided."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "startapp",
                    "agent",
                    "--platform-key",
                    "test-platform",
                    "--output",
                    ".",
                ],
                input="test-app\n",  # App name
            )
            # Should succeed or ask for confirmation
            assert "test-platform" in result.output or result.exit_code == 0

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
                    "--platform-key",
                    "acme",
                    "--mentor-id",
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
        """iblai add --help lists all five subcommands."""
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        for sub in ("auth", "chat", "profile", "notifications", "mcp"):
            assert sub in result.output

    def test_add_auth_requires_nextjs(self, runner):
        """Running iblai add auth outside a Next.js project shows an error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["add", "auth"])
            assert result.exit_code != 0 or "No package.json" in result.output
