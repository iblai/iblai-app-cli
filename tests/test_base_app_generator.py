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
        assert "ChatWidget" in content
        assert "ProfileDropdown" in content

    def test_no_chat_components(self, generated_dir):
        assert not (generated_dir / "components" / "chat").exists()

    def test_no_agent_routes(self, generated_dir):
        assert not (generated_dir / "app" / "(app)" / "platform").exists()

    def test_no_navbar(self, generated_dir):
        assert not (generated_dir / "components" / "navbar.tsx").exists()

    def test_no_sidebar(self, generated_dir):
        assert not (generated_dir / "components" / "app-sidebar.tsx").exists()

    def test_store_has_core_and_mentor_but_no_chat(self, generated_dir):
        store = (generated_dir / "store" / "index.ts").read_text()
        assert "coreApiSlice" in store
        assert "mentorReducer" in store
        assert "mentorMiddleware" in store
        # Chat-specific slices should NOT be in the base store
        assert "chatSliceReducerShared" not in store
        assert "filesReducer" not in store

    def test_providers_structure(self, generated_dir):
        providers = (generated_dir / "providers" / "index.tsx").read_text()
        assert "AuthProvider" in providers
        assert "TenantProvider" in providers
        # TenantProvider handles tenant fetching and exposes TenantContext
        assert "handleTenantSwitch" in providers
        assert "saveCurrentTenant" in providers
        assert "saveUserTenants" in providers
        assert "getCurrentTenant" in providers
        # MentorProvider not included
        assert "<MentorProvider" not in providers
        # initializeDataLayer called with 5 args (data-layer v1.2+ signature)
        assert "config.lmsUrl()," in providers

    def test_env_example_no_agent_id(self, generated_dir):
        env = (generated_dir / ".env.example").read_text()
        assert "NEXT_PUBLIC_DEFAULT_AGENT_ID" not in env
        assert "NEXT_PUBLIC_MAIN_TENANT_KEY=acme" in env

    def test_iblai_config_shim_exists(self, generated_dir):
        shim = generated_dir / "lib" / "iblai" / "config.ts"
        assert shim.exists()
        content = shim.read_text()
        assert "@/lib/config" in content

    def test_iblai_auth_utils_shim_exists(self, generated_dir):
        shim = generated_dir / "lib" / "iblai" / "auth-utils.ts"
        assert shim.exists()
        content = shim.read_text()
        assert "redirectToAuthSpa" in content
        assert "handleLogout" in content

    def test_generates_chat_widget(self, generated_dir):
        path = generated_dir / "components" / "iblai" / "chat-widget.tsx"
        assert path.exists()
        content = path.read_text()
        assert "mentor-ai" in content
        assert "@iblai/iblai-web-mentor" in content

    def test_generates_profile_dropdown(self, generated_dir):
        path = generated_dir / "components" / "iblai" / "profile-dropdown.tsx"
        assert path.exists()
        content = path.read_text()
        assert "UserProfileDropdown" in content
        assert "ProfileDropdown" in content  # renamed from IblaiProfileDropdown

    def test_generates_notification_bell(self, generated_dir):
        path = generated_dir / "components" / "iblai" / "notification-bell.tsx"
        assert path.exists()
        assert "NotificationDropdown" in path.read_text()

    def test_package_json_has_web_mentor(self, generated_dir):
        pkg = json.loads((generated_dir / "package.json").read_text())
        assert "@iblai/iblai-web-mentor" in pkg["dependencies"]

    def test_config_no_agent_url(self, generated_dir):
        config = (generated_dir / "lib" / "config.ts").read_text()
        assert "mainTenantKey" in config
        assert "agentUrl" not in config
        assert "defaultAgentId" not in config

    def test_generates_components_json(self, generated_dir):
        cj = json.loads((generated_dir / "components.json").read_text())
        assert cj["$schema"] == "https://ui.shadcn.com/schema.json"

    def test_generates_claude_skills(self, generated_dir):
        skills_dir = generated_dir / ".claude" / "skills"
        assert skills_dir.is_dir()
        skills = sorted(f.name for f in skills_dir.iterdir() if f.suffix == ".md")
        assert len(skills) == 12
        assert "iblai-setup.md" in skills
        assert "iblai-customize-chat.md" in skills
        assert "iblai-add-profile-page.md" in skills
        assert "iblai-add-account-page.md" in skills
        assert "iblai-add-analytics-page.md" in skills
        assert "iblai-add-notifications-page.md" in skills
        assert "iblai-add-component.md" in skills
        assert "iblai-add-test.md" in skills
        # startup skills removed — app is already generated when skills are present
        assert "iblai-startapp-base.md" not in skills
        assert "iblai-startapp-agent.md" not in skills

    def test_generates_opencode_skills(self, generated_dir):
        skills_dir = generated_dir / ".opencode" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        assert len(skill_dirs) == 12
        assert "iblai-setup" in skill_dirs
        assert "iblai-add-analytics-page" in skill_dirs
        assert "iblai-add-notifications-page" in skill_dirs
        assert "iblai-add-component" in skill_dirs
        assert "iblai-add-profile-page" in skill_dirs
        assert "iblai-add-account-page" in skill_dirs
        assert "iblai-add-test" in skill_dirs
        assert "iblai-startapp-base" not in skill_dirs
        assert "iblai-startapp-agent" not in skill_dirs
        skill_md = skills_dir / "iblai-setup" / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text()
        assert content.startswith("---")
        assert "name: iblai-setup" in content

    def test_generates_mcp_json(self, generated_dir):
        assert (generated_dir / ".mcp.json").exists()

    def test_generates_button_and_sonner(self, generated_dir):
        assert (generated_dir / "components" / "ui" / "button.tsx").exists()
        assert (generated_dir / "components" / "ui" / "sonner.tsx").exists()

    def test_pinned_dependency_versions(self, generated_dir):
        """Key dependencies are pinned to ensure SDK component compatibility."""
        pkg = json.loads((generated_dir / "package.json").read_text())
        deps = pkg["dependencies"]
        assert deps["next"] == "15.5.14"
        assert deps["react"] == "19.1.0"
        assert deps["react-dom"] == "19.1.0"
        assert deps["@reduxjs/toolkit"] == "2.11.2"
        assert deps["react-redux"] == "9.2.0"

    def test_generates_playwright_config(self, generated_dir):
        config = generated_dir / "e2e" / "playwright.config.ts"
        assert config.exists()
        assert "createPlaywrightConfig" in config.read_text()

    def test_generates_auth_setup(self, generated_dir):
        auth = generated_dir / "e2e" / "auth.setup.ts"
        assert auth.exists()
        assert "createAuthSetup" in auth.read_text()

    def test_generates_e2e_journeys(self, generated_dir):
        auth_j = generated_dir / "e2e" / "journeys" / "auth.journey.spec.ts"
        chat_j = generated_dir / "e2e" / "journeys" / "chat.journey.spec.ts"
        assert auth_j.exists()
        assert chat_j.exists()
        assert "axd_token" in auth_j.read_text()
        assert "mentor-ai" in chat_j.read_text()

    def test_e2e_scripts_in_package_json(self, generated_dir):
        pkg = json.loads((generated_dir / "package.json").read_text())
        assert "test:e2e" in pkg["scripts"]
        assert "test:e2e:ui" in pkg["scripts"]
        assert "@playwright/test" in pkg["devDependencies"]


class TestBaseAppCLI:
    """Tests for the base template via the CLI."""

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner

        return CliRunner()

    def test_agent_in_startapp_help(self, runner):
        from iblai_cli.cli import cli

        result = runner.invoke(cli, ["startapp", "--help"])
        assert result.exit_code == 0
        assert "agent" in result.output
        # base is no longer exposed as a CLI option (generator still exists internally)
        assert "base" not in result.output
