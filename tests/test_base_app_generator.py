"""Tests for the 'base' template generator."""

import json

import pytest

from iblai_cli.generators.base_app import BaseAppGenerator


class TestBaseAppGenerator:
    """Tests for BaseAppGenerator — minimal Next.js app with IBL.ai auth."""

    @pytest.fixture
    def generated_dir(self, tmp_path):
        output = tmp_path / "my-base-app"
        gen = BaseAppGenerator(
            app_name="my-base-app",
            platform_key="acme",
            output_dir=str(output),
        )
        gen.generate()
        return output

    def test_generates_directory(self, generated_dir):
        assert generated_dir.is_dir()

    def test_generates_package_json(self, generated_dir):
        pkg = json.loads((generated_dir / "package.json").read_text())
        assert pkg["name"] == "my-base-app"
        # Should NOT have chat-specific deps
        assert "react-markdown" not in pkg.get("dependencies", {})
        assert "remark-gfm" not in pkg.get("dependencies", {})
        # Should have platform deps
        assert "@iblai/iblai-js" in pkg["dependencies"]
        assert "@reduxjs/toolkit" in pkg["dependencies"]
        assert "next" in pkg["dependencies"]
        assert "react" in pkg["dependencies"]

    def test_generates_app_structure(self, generated_dir):
        for d in ("app", "components", "lib", "providers", "store", "hooks", "public"):
            assert (generated_dir / d).is_dir(), f"Missing directory: {d}"

    def test_generates_route_groups(self, generated_dir):
        assert (generated_dir / "app" / "(app)").is_dir()
        assert (generated_dir / "app" / "(auth)").is_dir()

    def test_generates_sso_callback(self, generated_dir):
        sso = generated_dir / "app" / "(auth)" / "sso-login-complete" / "page.tsx"
        assert sso.exists()
        assert "SsoLogin" in sso.read_text()

    def test_home_page_has_greeting_and_email(self, generated_dir):
        page = generated_dir / "app" / "(app)" / "page.tsx"
        assert page.exists()
        content = page.read_text()
        assert "Welcome" in content
        assert "useUsername" in content
        assert "email" in content
        assert "userData" in content
        assert "iblai add" in content

    def test_no_chat_components(self, generated_dir):
        assert not (generated_dir / "components" / "chat").exists()

    def test_no_agent_routes(self, generated_dir):
        assert not (generated_dir / "app" / "(app)" / "platform").exists()

    def test_no_navbar(self, generated_dir):
        assert not (generated_dir / "components" / "navbar.tsx").exists()

    def test_no_sidebar(self, generated_dir):
        assert not (generated_dir / "components" / "app-sidebar.tsx").exists()

    def test_store_no_chat_slices(self, generated_dir):
        store = (generated_dir / "store" / "index.ts").read_text()
        assert "coreApiSlice" in store
        assert "chatSliceReducerShared" not in store
        assert "filesReducer" not in store
        assert "mentorReducer" not in store

    def test_providers_no_mentor(self, generated_dir):
        providers = (generated_dir / "providers" / "index.tsx").read_text()
        assert "AuthProvider" in providers
        assert "TenantProvider" in providers
        # MentorProvider should not be imported or used (may appear in comments)
        assert (
            "import" not in providers
            or "MentorProvider" not in providers.split("import")[1]
            if "MentorProvider" in providers
            else True
        )
        assert "<MentorProvider" not in providers

    def test_env_example_no_agent_id(self, generated_dir):
        env = (generated_dir / ".env.example").read_text()
        assert "NEXT_PUBLIC_DEFAULT_AGENT_ID" not in env
        assert "NEXT_PUBLIC_MAIN_TENANT_KEY=acme" in env

    def test_config_no_agent_url(self, generated_dir):
        config = (generated_dir / "lib" / "config.ts").read_text()
        assert "mainTenantKey" in config
        assert "agentUrl" not in config
        assert "defaultAgentId" not in config

    def test_generates_components_json(self, generated_dir):
        cj = json.loads((generated_dir / "components.json").read_text())
        assert cj["$schema"] == "https://ui.shadcn.com/schema.json"

    def test_generates_mcp_json(self, generated_dir):
        assert (generated_dir / ".mcp.json").exists()

    def test_generates_button_and_sonner(self, generated_dir):
        assert (generated_dir / "components" / "ui" / "button.tsx").exists()
        assert (generated_dir / "components" / "ui" / "sonner.tsx").exists()

    def test_pinned_dependency_versions(self, generated_dir):
        """Key dependencies are pinned to ensure SDK component compatibility."""
        pkg = json.loads((generated_dir / "package.json").read_text())
        deps = pkg["dependencies"]
        assert deps["next"] == "15.3.6"
        assert deps["react"] == "19.1.0"
        assert deps["react-dom"] == "19.1.0"
        assert deps["@reduxjs/toolkit"] == "2.7.0"
        assert deps["react-redux"] == "9.2.0"


class TestBaseAppCLI:
    """Tests for the base template via the CLI."""

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner

        return CliRunner()

    def test_base_in_startapp_help(self, runner):
        from iblai_cli.cli import cli

        result = runner.invoke(cli, ["startapp", "--help"])
        assert result.exit_code == 0
        assert "base" in result.output
        assert "agent" in result.output
