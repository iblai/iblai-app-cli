"""Tests for the 'base' template generator."""

import json

import pytest

from iblai.generators.base_app import BaseAppGenerator


class TestBaseAppGenerator:
    """Tests for BaseAppGenerator — minimal Next.js app with ibl.ai auth."""

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
        assert "resolveAppTenant" in providers
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
        assert len(skills) == 13
        assert "iblai-setup.md" in skills
        assert "iblai-add-profile.md" in skills
        assert "iblai-add-account.md" in skills
        assert "iblai-add-analytics.md" in skills
        assert "iblai-add-notification.md" in skills
        assert "iblai-add-component.md" in skills
        assert "iblai-add-test.md" in skills
        # startup skills removed — app is already generated when skills are present
        assert "iblai-startapp-base.md" not in skills
        assert "iblai-startapp-agent.md" not in skills

    def test_generates_opencode_skills(self, generated_dir):
        skills_dir = generated_dir / ".opencode" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        assert len(skill_dirs) == 13
        assert "iblai-setup" in skill_dirs
        assert "iblai-add-analytics" in skill_dirs
        assert "iblai-add-notification" in skill_dirs
        assert "iblai-add-component" in skill_dirs
        assert "iblai-add-profile" in skill_dirs
        assert "iblai-add-account" in skill_dirs
        assert "iblai-add-test" in skill_dirs
        # OpenCode SKILL.md is a symlink to skills/<name>.md
        skill_md = skills_dir / "iblai-setup" / "SKILL.md"
        assert skill_md.exists()
        assert skill_md.is_symlink()

    def test_generates_skills_directory(self, generated_dir):
        """Central skills/ directory with categorized subdirectories."""
        skills_dir = generated_dir / "skills"
        assert skills_dir.is_dir()
        assert (skills_dir / "README.md").exists()
        # Check categorized subdirectories (pages merged into components)
        assert (skills_dir / "setup").is_dir()
        assert (skills_dir / "components").is_dir()
        assert (skills_dir / "builds").is_dir()
        assert (skills_dir / "testing").is_dir()
        assert not (skills_dir / "pages").exists()
        # Check specific files
        assert (skills_dir / "setup" / "iblai-setup.md").exists()
        assert (skills_dir / "components" / "iblai-add-auth.md").exists()
        assert (skills_dir / "components" / "iblai-add-account.md").exists()
        assert (skills_dir / "builds" / "iblai-build-windows-msix.md").exists()
        assert (skills_dir / "testing" / "iblai-add-test.md").exists()
        # Total count
        all_skills = sorted(skills_dir.rglob("*.md"))
        skill_files = [f for f in all_skills if f.name != "README.md"]
        assert len(skill_files) == 17

    def test_generates_cursor_rules(self, generated_dir):
        """Cursor .cursor/rules/ directory with symlinks."""
        rules_dir = generated_dir / ".cursor" / "rules"
        assert rules_dir.is_dir()
        link = rules_dir / "iblai-setup.md"
        assert link.exists()
        assert link.is_symlink()

    def test_generates_mcp_json(self, generated_dir):
        assert (generated_dir / ".mcp.json").exists()

    def test_generates_claude_md(self, generated_dir):
        claude_md = generated_dir / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "MCP Server" in content
        assert "pnpm dev" in content
        assert "initializeDataLayer" in content
        assert "DO NOT INITIALIZE GIT" in content

    def test_generates_button_and_sonner(self, generated_dir):
        assert (generated_dir / "components" / "ui" / "button.tsx").exists()
        assert (generated_dir / "components" / "ui" / "sonner.tsx").exists()

    def test_pinned_dependency_versions(self, generated_dir):
        """Key dependencies are pinned to ensure SDK component compatibility."""
        pkg = json.loads((generated_dir / "package.json").read_text())
        deps = pkg["dependencies"]
        assert deps["next"] == "^16.2.1"
        assert deps["react"] == "^19.2.4"
        assert deps["react-dom"] == "^19.2.4"
        assert deps["@reduxjs/toolkit"] == "2.11.2"
        assert deps["react-redux"] == "9.2.0"

    def test_generates_playwright_config(self, generated_dir):
        config = generated_dir / "e2e" / "playwright.config.ts"
        assert config.exists()
        content = config.read_text()
        assert "defineConfig" in content
        assert "setup-chromium" in content

    def test_generates_auth_setup(self, generated_dir):
        auth = generated_dir / "e2e" / "auth.setup.ts"
        assert auth.exists()
        content = auth.read_text()
        assert "authenticate" in content
        assert "axd_token" in content

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


class TestTauriNextConfig:
    """Tests for tauri flag effect on next.config.ts."""

    def test_tauri_flag_produces_static_export(self, tmp_path):
        """When builds=True, next.config.ts has output:'export' and no stubs."""
        from iblai.generators.base_app import BaseAppGenerator

        gen = BaseAppGenerator(
            app_name="test",
            platform_key="test",
            output_dir=str(tmp_path / "app"),
            builds=True,
        )
        gen.generate()
        config = (tmp_path / "app" / "next.config.ts").read_text()
        assert 'output: "export"' in config
        assert '@tauri-apps/api/core"] = false' not in config
        assert '@tauri-apps/api/event"] = false' not in config

    def test_no_tauri_flag_no_stubs_or_export(self, tmp_path):
        """When builds=False, next.config.ts has no stubs and no export."""
        from iblai.generators.base_app import BaseAppGenerator

        gen = BaseAppGenerator(
            app_name="test",
            platform_key="test",
            output_dir=str(tmp_path / "app"),
            builds=False,
        )
        gen.generate()
        config = (tmp_path / "app" / "next.config.ts").read_text()
        assert 'output: "export"' not in config
        assert '@tauri-apps/api/core"] = false' not in config
        assert '@tauri-apps/api/event"] = false' not in config

    def test_tauri_flag_adds_tauri_deps_to_package_json(self, tmp_path):
        """When builds=True, package.json includes Tauri deps and scripts."""
        import json
        from iblai.generators.base_app import BaseAppGenerator

        gen = BaseAppGenerator(
            app_name="test",
            platform_key="test",
            output_dir=str(tmp_path / "app"),
            builds=True,
        )
        gen.generate()
        pkg = json.loads((tmp_path / "app" / "package.json").read_text())
        assert "@tauri-apps/api" in pkg["dependencies"]
        assert "@tauri-apps/cli" in pkg["devDependencies"]
        assert "tauri:dev" in pkg["scripts"]

    def test_no_tauri_flag_includes_api_excludes_cli(self, tmp_path):
        """When builds=False, package.json has @tauri-apps/api but no CLI/scripts."""
        import json
        from iblai.generators.base_app import BaseAppGenerator

        gen = BaseAppGenerator(
            app_name="test",
            platform_key="test",
            output_dir=str(tmp_path / "app"),
            builds=False,
        )
        gen.generate()
        pkg = json.loads((tmp_path / "app" / "package.json").read_text())
        assert "@tauri-apps/api" in pkg.get("dependencies", {})
        assert "@tauri-apps/cli" not in pkg.get("devDependencies", {})
        assert "tauri:dev" not in pkg.get("scripts", {})


class TestBaseAppCLI:
    """Tests for the base template via the CLI."""

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner

        return CliRunner()

    def test_agent_in_startapp_help(self, runner):
        from iblai.cli import cli

        result = runner.invoke(cli, ["startapp", "--help"])
        assert result.exit_code == 0
        assert "agent" in result.output
        # base is no longer exposed as a CLI option (generator still exists internally)
        assert "base" not in result.output
