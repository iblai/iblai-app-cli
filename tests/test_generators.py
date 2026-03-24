"""Tests for generator classes."""

import os
import pytest
from pathlib import Path
from iblai_cli.generators.agent import AgentAppGenerator


class TestBaseGenerator:
    """Test suite for BaseGenerator class."""

    def test_get_context(self):
        """Test context generation."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="test-platform",
            mentor_id="mentor-123",
            output_dir="/tmp/test",
        )

        context = generator.get_context()

        assert context["app_name"] == "test-app"
        assert context["platform_key"] == "test-platform"
        assert context["mentor_id"] == "mentor-123"
        assert context["has_mentor_id"] is True

    def test_get_context_without_mentor_id(self):
        """Test context generation without mentor ID."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="test-platform",
            output_dir="/tmp/test",
        )

        context = generator.get_context()

        assert context["app_name"] == "test-app"
        assert context["platform_key"] == "test-platform"
        assert context["mentor_id"] is None
        assert context["has_mentor_id"] is False


class TestAgentAppGenerator:
    """Test suite for AgentAppGenerator class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Fixture for temporary directory."""
        return tmp_path / "test-agent-app"

    def test_generator_initialization(self, temp_dir):
        """Test that generator initializes correctly."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            mentor_id="agent-1",
            output_dir=str(temp_dir),
        )

        assert generator.app_name == "test-app"
        assert generator.platform_key == "acme"
        assert generator.mentor_id == "agent-1"
        assert generator.output_dir == temp_dir

    def test_generate_creates_directory(self, temp_dir):
        """Test that generate() creates the output directory."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_generate_creates_package_json(self, temp_dir):
        """Test that generate() creates package.json."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        package_json = temp_dir / "package.json"
        assert package_json.exists()

        # Verify content contains app name
        content = package_json.read_text()
        assert "test-app" in content

    def test_generate_creates_app_structure(self, temp_dir):
        """Test that generate() creates proper app directory structure."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            mentor_id="agent-1",
            output_dir=str(temp_dir),
        )

        generator.generate()

        # Check essential directories exist
        assert (temp_dir / "app").exists()
        assert (temp_dir / "components").exists()
        assert (temp_dir / "lib").exists()
        assert (temp_dir / "providers").exists()
        assert (temp_dir / "store").exists()

    def test_generate_creates_essential_files(self, temp_dir):
        """Test that generate() creates essential configuration files."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        # Check essential files
        essential_files = [
            "package.json",
            "tsconfig.json",
            "next.config.mjs",
            "tailwind.config.ts",
            ".env.example",
            ".gitignore",
        ]

        for file_name in essential_files:
            assert (temp_dir / file_name).exists(), f"Missing {file_name}"

    def test_generate_creates_iblai_components(self, temp_dir):
        """Test that generate() creates the iblai/ components using ChatWidget."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        # Custom chat components are gone — replaced by the ChatWidget web component
        assert not (temp_dir / "components" / "chat").exists()

        # ChatWidget + profile + notifications should be generated
        assert (temp_dir / "components" / "iblai" / "chat-widget.tsx").exists()
        assert (temp_dir / "components" / "iblai" / "profile-dropdown.tsx").exists()
        assert (temp_dir / "components" / "iblai" / "notification-bell.tsx").exists()

        # Verify the ChatWidget uses mentor-ai
        widget = (temp_dir / "components" / "iblai" / "chat-widget.tsx").read_text()
        assert "mentor-ai" in widget
        assert "@iblai/iblai-web-mentor" in widget
        assert 'authrelyonhost="true"' in widget

    def test_generate_with_mentor_id_in_env(self, temp_dir):
        """Test that mentor ID appears in env file when provided."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            mentor_id="my-agent-123",
            output_dir=str(temp_dir),
        )

        generator.generate()

        env_example = temp_dir / ".env.example"
        content = env_example.read_text()

        assert "my-agent-123" in content
        assert "NEXT_PUBLIC_DEFAULT_AGENT_ID" in content

    def test_generate_without_mentor_id_in_env(self, temp_dir):
        """Test that mentor ID section is excluded when not provided."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        env_example = temp_dir / ".env.example"
        content = env_example.read_text()

        # Should not contain default agent ID line
        assert "NEXT_PUBLIC_DEFAULT_AGENT_ID" not in content

    def test_generate_creates_ui_components(self, temp_dir):
        """Test that generate() creates UI component re-exports."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="acme",
            output_dir=str(temp_dir),
        )

        generator.generate()

        # Check UI components
        ui_components = [
            "components/ui/button.tsx",
            "components/ui/sidebar.tsx",
            "components/ui/avatar.tsx",
            "components/ui/dropdown-menu.tsx",
            "components/ui/input.tsx",
            "components/ui/textarea.tsx",
            "components/ui/skeleton.tsx",
        ]

        for component_path in ui_components:
            file_path = temp_dir / component_path
            assert file_path.exists(), f"Missing {component_path}"

    def test_platform_key_in_config(self, temp_dir):
        """Test that platform key appears in config files."""
        generator = AgentAppGenerator(
            app_name="test-app",
            platform_key="my-platform",
            output_dir=str(temp_dir),
        )

        generator.generate()

        # Check .env.example
        env_file = temp_dir / ".env.example"
        env_content = env_file.read_text()
        assert "my-platform" in env_content

        # Check config.ts
        config_file = temp_dir / "lib" / "config.ts"
        config_content = config_file.read_text()
        assert "my-platform" in config_content


class TestAgentRouteGroups:
    """Tests for the Next.js route group structure (app/(app)/ and app/(auth)/)."""

    @pytest.fixture
    def generated_dir(self, tmp_path):
        from iblai_cli.generators.agent import AgentAppGenerator

        output = tmp_path / "route-group-app"
        gen = AgentAppGenerator(
            app_name="route-group-app",
            platform_key="acme",
            mentor_id="test-agent",
            output_dir=str(output),
        )
        gen.generate()
        return output

    def test_generate_creates_route_groups(self, generated_dir):
        """Both (app) and (auth) route group directories exist."""
        assert (generated_dir / "app" / "(app)").is_dir()
        assert (generated_dir / "app" / "(auth)").is_dir()

    def test_sso_page_in_auth_route_group(self, generated_dir):
        """SSO callback page is inside (auth) route group, outside auth providers."""
        sso = generated_dir / "app" / "(auth)" / "sso-login-complete" / "page.tsx"
        assert sso.exists()
        content = sso.read_text()
        assert "SsoLogin" in content

    def test_platform_pages_in_app_route_group(self, generated_dir):
        """Platform/agent pages are inside (app) route group, wrapped by AppShell."""
        assert (
            generated_dir
            / "app"
            / "(app)"
            / "platform"
            / "[tenantKey]"
            / "[agentId]"
            / "page.tsx"
        ).exists()
        assert (
            generated_dir / "app" / "(app)" / "platform" / "[tenantKey]" / "page.tsx"
        ).exists()

    def test_authenticated_layout_in_app_group(self, generated_dir):
        """(app)/layout.tsx exists and wraps children with AppShell."""
        layout = generated_dir / "app" / "(app)" / "layout.tsx"
        assert layout.exists()
        content = layout.read_text()
        assert "AppShell" in content
