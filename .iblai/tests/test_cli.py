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
        """Test that CLI version command shows repo and commit."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
        assert "github.com/iblai/iblai-app-cli" in result.output
        assert "Commit:" in result.output

    def test_cli_info(self, runner):
        """Test that iblai info shows version, repo, commit, platform."""
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "github.com/iblai/iblai-app-cli" in result.output
        assert "Python" in result.output
        assert "Platform" in result.output

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
        """iblai add --help lists all eight subcommands."""
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        for sub in (
            "auth",
            "chat",
            "profile",
            "notifications",
            "account",
            "analytics",
            "mcp",
            "builds",
        ):
            assert sub in result.output

    def test_init_help(self, runner):
        """iblai init --help shows the command."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "AI-assisted" in result.output

    def test_open_help(self, runner):
        """iblai open --help shows targets."""
        result = runner.invoke(cli, ["open", "--help"])
        assert result.exit_code == 0
        assert "app" in result.output
        assert "docs" in result.output

    def test_open_in_main_help(self, runner):
        """iblai --help lists open and init commands."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "open" in result.output
        assert "init" in result.output

    def test_config_show_help(self, runner):
        """iblai config show --help works."""
        result = runner.invoke(cli, ["config", "show", "--help"])
        assert result.exit_code == 0
        assert (
            "effective configuration" in result.output.lower()
            or "configuration" in result.output.lower()
        )

    def test_config_set_help(self, runner):
        """iblai config set --help works."""
        result = runner.invoke(cli, ["config", "set", "--help"])
        assert result.exit_code == 0
        assert "KEY" in result.output
        assert "VALUE" in result.output

    def test_config_show_displays_variables(self, runner):
        """iblai config show prints known variables."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["config", "show"])
            assert result.exit_code == 0
            assert "NEXT_PUBLIC_API_BASE_URL" in result.output
            assert "NEXT_PUBLIC_AUTH_URL" in result.output
            assert "NEXT_PUBLIC_MAIN_TENANT_KEY" in result.output

    def test_config_set_creates_env_local(self, runner):
        """iblai config set writes to .env.local."""
        import os

        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["config", "set", "NEXT_PUBLIC_MAIN_TENANT_KEY", "acme"]
            )
            assert result.exit_code == 0
            assert "Set" in result.output
            # Verify file was created
            content = open(".env.local").read()
            assert "NEXT_PUBLIC_MAIN_TENANT_KEY=acme" in content

    def test_config_in_main_help(self, runner):
        """iblai --help lists config command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "config" in result.output

    def test_add_auth_requires_nextjs(self, runner):
        """Running iblai add auth outside a Next.js project shows an error."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["add", "auth"])
            assert result.exit_code != 0 or "No package.json" in result.output
