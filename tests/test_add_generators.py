"""Tests for iblai add generators -- auth, chat, profile, notifications, mcp."""

import json
import os

import pytest

from iblai_cli.project_detector import ProjectInfo


def _make_project(tmp_path, src_dir=None):
    """Create a minimal Next.js project and return ProjectInfo."""
    root = tmp_path / "project"
    root.mkdir()
    if src_dir:
        (root / src_dir / "app").mkdir(parents=True)
    else:
        (root / "app").mkdir()
    pkg = {
        "dependencies": {"next": "15.0.0"},
        "devDependencies": {"typescript": "5.0.0"},
    }
    (root / "package.json").write_text(json.dumps(pkg))
    return ProjectInfo(
        root=root,
        framework="nextjs",
        has_app_router=True,
        has_typescript=True,
        src_dir=src_dir,
    )


# ---------------------------------------------------------------------------
# Auth generator
# ---------------------------------------------------------------------------


class TestAddAuthGenerator:
    """Tests for AddAuthGenerator."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    @pytest.fixture
    def generated(self, project):
        from iblai_cli.generators.add_auth import AddAuthGenerator

        gen = AddAuthGenerator(project, platform_key="acme")
        created = gen.generate()
        return project, created

    def test_auth_generates_seven_files(self, generated):
        _, created = generated
        assert len(created) == 7

    def test_auth_creates_sso_page(self, generated):
        project, _ = generated
        path = project.app_dir / "sso-login-complete" / "page.tsx"
        assert path.exists()
        content = path.read_text()
        assert "SsoLogin" in content

    def test_auth_creates_config(self, generated):
        project, _ = generated
        path = project.lib_dir / "iblai" / "config.ts"
        assert path.exists()
        content = path.read_text()
        assert "NEXT_PUBLIC_API_BASE_URL" in content
        assert "mainTenantKey" in content

    def test_auth_creates_storage_service(self, generated):
        project, _ = generated
        path = project.lib_dir / "iblai" / "storage-service.ts"
        assert path.exists()
        content = path.read_text()
        assert "LocalStorageService" in content

    def test_auth_creates_auth_utils(self, generated):
        project, _ = generated
        path = project.lib_dir / "iblai" / "auth-utils.ts"
        assert path.exists()
        content = path.read_text()
        assert "redirectToAuthSpa" in content
        assert "hasNonExpiredAuthToken" in content
        # Verify the fix: no token → return false (not true)
        assert "if (!token) return false" in content

    def test_auth_creates_store(self, generated):
        project, _ = generated
        path = project.store_dir / "iblai-store.ts"
        assert path.exists()
        content = path.read_text()
        assert "coreApiSlice" in content
        assert "configureStore" in content

    def test_auth_creates_providers(self, generated):
        project, _ = generated
        path = project.providers_dir / "iblai-providers.tsx"
        assert path.exists()
        content = path.read_text()
        assert "AuthProvider" in content
        assert "TenantProvider" in content
        assert "IblaiProviders" in content

    def test_auth_creates_styles(self, generated):
        project, _ = generated
        path = project.app_dir / "iblai-styles.css"
        assert path.exists()
        content = path.read_text()
        assert "@iblai/iblai-js/web-containers/styles" in content


# ---------------------------------------------------------------------------
# Chat generator
# ---------------------------------------------------------------------------


class TestAddChatGenerator:
    """Tests for AddChatGenerator."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    @pytest.fixture
    def widget_content(self, project):
        from iblai_cli.generators.add_chat import AddChatGenerator

        gen = AddChatGenerator(project)
        gen.generate()
        path = project.components_dir / "iblai" / "chat-widget.tsx"
        return path.read_text()

    def test_chat_generates_widget(self, project):
        from iblai_cli.generators.add_chat import AddChatGenerator

        created = AddChatGenerator(project).generate()
        assert len(created) == 1
        assert (project.components_dir / "iblai" / "chat-widget.tsx").exists()

    def test_chat_widget_has_session_management(self, widget_content):
        assert "sessionId" in widget_content
        assert "cachedSessionId" in widget_content
        assert "onStartNewChat" in widget_content

    def test_chat_widget_has_markdown(self, widget_content):
        assert "ReactMarkdown" in widget_content
        assert "remarkGfm" in widget_content

    def test_chat_widget_uses_config(self, widget_content):
        assert "config.baseWsUrl()" in widget_content
        assert "config.mainTenantKey()" in widget_content


# ---------------------------------------------------------------------------
# Profile generator
# ---------------------------------------------------------------------------


class TestAddProfileGenerator:
    """Tests for AddProfileGenerator."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    @pytest.fixture
    def profile_content(self, project):
        from iblai_cli.generators.add_profile import AddProfileGenerator

        AddProfileGenerator(project).generate()
        return (project.components_dir / "iblai" / "profile-dropdown.tsx").read_text()

    def test_profile_generates_dropdown(self, project):
        from iblai_cli.generators.add_profile import AddProfileGenerator

        created = AddProfileGenerator(project).generate()
        assert len(created) == 1
        assert (project.components_dir / "iblai" / "profile-dropdown.tsx").exists()

    def test_profile_uses_sdk_component(self, profile_content):
        assert "UserProfileDropdown" in profile_content

    def test_profile_has_required_props(self, profile_content):
        assert "onTenantUpdate" in profile_content
        assert "onLogout" in profile_content


# ---------------------------------------------------------------------------
# Notifications generator
# ---------------------------------------------------------------------------


class TestAddNotificationsGenerator:
    """Tests for AddNotificationsGenerator."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    def test_notifications_generates_bell(self, project):
        from iblai_cli.generators.add_notifications import AddNotificationsGenerator

        created = AddNotificationsGenerator(project).generate()
        assert len(created) == 1
        assert (project.components_dir / "iblai" / "notification-bell.tsx").exists()

    def test_notifications_uses_sdk_component(self, project):
        from iblai_cli.generators.add_notifications import AddNotificationsGenerator

        AddNotificationsGenerator(project).generate()
        content = (
            project.components_dir / "iblai" / "notification-bell.tsx"
        ).read_text()
        assert "NotificationDropdown" in content


# ---------------------------------------------------------------------------
# MCP generator
# ---------------------------------------------------------------------------


class TestAddMcpGenerator:
    """Tests for AddMcpGenerator."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    @pytest.fixture
    def generated(self, project):
        from iblai_cli.generators.add_mcp import AddMcpGenerator

        created = AddMcpGenerator(project).generate()
        return project, created

    def test_mcp_generates_config(self, generated):
        project, _ = generated
        assert (project.root / ".mcp.json").exists()

    def test_mcp_config_is_valid_json(self, generated):
        project, _ = generated
        data = json.loads((project.root / ".mcp.json").read_text())
        assert "mcpServers" in data
        assert "iblai-js-mcp" in data["mcpServers"]

    def test_mcp_config_uses_npx(self, generated):
        project, _ = generated
        data = json.loads((project.root / ".mcp.json").read_text())
        server = data["mcpServers"]["iblai-js-mcp"]
        assert server["command"] == "npx"
        assert "@iblai/mcp" in server["args"]

    def test_mcp_generates_skills(self, generated):
        project, _ = generated
        skills_dir = project.root / ".claude" / "skills"
        assert skills_dir.is_dir()
        skills = sorted(f.name for f in skills_dir.iterdir() if f.suffix == ".md")
        assert len(skills) == 5

    def test_mcp_skill_filenames(self, generated):
        project, _ = generated
        skills_dir = project.root / ".claude" / "skills"
        expected = {
            "iblai-add-auth.md",
            "iblai-add-chat.md",
            "iblai-add-notifications.md",
            "iblai-add-profile.md",
            "iblai-setup.md",
        }
        actual = {f.name for f in skills_dir.iterdir() if f.suffix == ".md"}
        assert actual == expected


# ---------------------------------------------------------------------------
# src/ directory support
# ---------------------------------------------------------------------------


class TestAddGeneratorsSrcDir:
    """Verify generators respect src/ directory layout."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path, src_dir="src")

    def test_auth_respects_src_dir(self, project):
        from iblai_cli.generators.add_auth import AddAuthGenerator

        created = AddAuthGenerator(project, platform_key="acme").generate()
        assert any("src/lib/iblai/config.ts" in f for f in created)
        assert (project.root / "src" / "lib" / "iblai" / "config.ts").exists()

    def test_chat_respects_src_dir(self, project):
        from iblai_cli.generators.add_chat import AddChatGenerator

        AddChatGenerator(project).generate()
        assert (
            project.root / "src" / "components" / "iblai" / "chat-widget.tsx"
        ).exists()

    def test_profile_respects_src_dir(self, project):
        from iblai_cli.generators.add_profile import AddProfileGenerator

        AddProfileGenerator(project).generate()
        assert (
            project.root / "src" / "components" / "iblai" / "profile-dropdown.tsx"
        ).exists()
