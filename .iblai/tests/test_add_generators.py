"""Tests for iblai add generators -- auth, chat, profile, notifications, mcp."""

import json
import os
from unittest.mock import patch

import pytest

from iblai.project_detector import ProjectInfo


@pytest.fixture(autouse=True)
def mock_subprocess():
    """Mock subprocess.run so install_packages doesn't run real package managers."""
    with patch("iblai.package_manager.subprocess.run") as mock_run:
        mock_run.return_value = None
        yield mock_run


def _make_project(tmp_path, src_dir=None):
    """Create a minimal Next.js project and return ProjectInfo."""
    root = tmp_path / "project"
    root.mkdir()
    app_dir = root / (src_dir or "") / "app" if src_dir else root / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    pkg = {
        "dependencies": {"next": "15.0.0"},
        "devDependencies": {"typescript": "5.0.0"},
    }
    (root / "package.json").write_text(json.dumps(pkg))

    # Create globals.css, next.config.ts, and store/index.ts so patching has targets
    (app_dir / "globals.css").write_text('@import "tailwindcss";\n')
    (root / "next.config.ts").write_text(
        'import type { NextConfig } from "next";\n\n'
        "const nextConfig: NextConfig = {\n"
        "  webpack: (config) => {\n"
        "    return config;\n"
        "  },\n"
        "};\n\n"
        "export default nextConfig;\n"
    )
    store_dir = root / (src_dir or "") / "store" if src_dir else root / "store"
    store_dir.mkdir(parents=True, exist_ok=True)
    (store_dir / "index.ts").write_text(
        'import { configureStore } from "@reduxjs/toolkit";\n'
        "import {\n  coreApiSlice,\n  mentorReducer,\n  mentorMiddleware,\n"
        '} from "@iblai/iblai-js/data-layer";\n\n'
        "export const makeStore = () => {\n"
        "  return configureStore({\n"
        "    reducer: {\n"
        "      [coreApiSlice.reducerPath]: coreApiSlice.reducer,\n"
        "      ...mentorReducer,\n"
        "    },\n"
        "    middleware: (getDefaultMiddleware) =>\n"
        "      getDefaultMiddleware({ serializableCheck: false })\n"
        "        .concat(coreApiSlice.middleware)\n"
        "        .concat(...mentorMiddleware),\n"
        "  });\n"
        "};\n"
    )
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
        from iblai.generators.add_auth import AddAuthGenerator

        gen = AddAuthGenerator(project, platform_key="acme")
        created = gen.generate()
        return project, created

    def test_auth_generates_all_files(self, generated):
        _, created = generated
        # 7 generated files + lib/iblai/tenant.ts + next.config (patched)
        # + globals.css (patched) + .env.local + SDK symlink
        # + vitest.config.ts + __tests__/source-paths.test.ts
        assert len(created) == 14

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
        from iblai.generators.add_chat import AddChatGenerator

        gen = AddChatGenerator(project)
        gen.generate()
        path = project.components_dir / "iblai" / "chat-widget.tsx"
        return path.read_text()

    def test_chat_generates_widget(self, project):
        from iblai.generators.add_chat import AddChatGenerator

        created = AddChatGenerator(project).generate()
        assert (project.components_dir / "iblai" / "chat-widget.tsx").exists()
        assert any("chat-widget.tsx" in f for f in created)

    def test_chat_widget_uses_mentor_ai_web_component(self, widget_content):
        assert "mentor-ai" in widget_content
        assert "@iblai/iblai-web-mentor" in widget_content
        assert 'authrelyonhost="true"' in widget_content

    def test_chat_widget_uses_config(self, widget_content):
        assert "config.authUrl()" in widget_content
        assert "config.lmsUrl()" in widget_content
        assert "resolveAppTenant" in widget_content
        assert "config.platformBaseDomain" in widget_content


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
        from iblai.generators.add_profile import AddProfileGenerator

        AddProfileGenerator(project).generate()
        return (project.components_dir / "iblai" / "profile-dropdown.tsx").read_text()

    def test_profile_generates_dropdown(self, project):
        from iblai.generators.add_profile import AddProfileGenerator

        created = AddProfileGenerator(project).generate()
        assert len(created) == 1
        assert (project.components_dir / "iblai" / "profile-dropdown.tsx").exists()

    def test_profile_uses_sdk_component(self, profile_content):
        assert "UserProfileDropdown" in profile_content

    def test_profile_exports_profile_dropdown(self, profile_content):
        assert "ProfileDropdown" in profile_content

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
        from iblai.generators.add_notifications import AddNotificationsGenerator

        created = AddNotificationsGenerator(project).generate()
        assert len(created) == 1
        assert (project.components_dir / "iblai" / "notification-bell.tsx").exists()

    def test_notifications_uses_sdk_component(self, project):
        from iblai.generators.add_notifications import AddNotificationsGenerator

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
        from iblai.generators.add_mcp import AddMcpGenerator

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
        assert "playwright" in data["mcpServers"]
        assert "shadcn" in data["mcpServers"]

    def test_mcp_config_uses_npx(self, generated):
        project, _ = generated
        data = json.loads((project.root / ".mcp.json").read_text())
        server = data["mcpServers"]["iblai-js-mcp"]
        assert server["command"] == "npx"
        assert "@iblai/mcp" in server["args"]

    def test_mcp_config_playwright_server(self, generated):
        project, _ = generated
        data = json.loads((project.root / ".mcp.json").read_text())
        server = data["mcpServers"]["playwright"]
        assert server["command"] == "npx"
        assert "@playwright/mcp@latest" in server["args"]

    def test_mcp_config_shadcn_server(self, generated):
        project, _ = generated
        data = json.loads((project.root / ".mcp.json").read_text())
        server = data["mcpServers"]["shadcn"]
        assert server["command"] == "npx"
        assert "shadcn@latest" in server["args"]
        assert "mcp" in server["args"]

    def test_mcp_generates_claude_skills(self, generated):
        project, _ = generated
        skills_dir = project.root / ".claude" / "skills"
        assert skills_dir.is_dir()
        skills = sorted(f.name for f in skills_dir.iterdir() if f.suffix == ".md")
        assert len(skills) == 13

    def test_mcp_claude_skill_filenames(self, generated):
        project, _ = generated
        skills_dir = project.root / ".claude" / "skills"
        expected = {
            "iblai-add-account.md",
            "iblai-add-analytics.md",
            "iblai-add-auth.md",
            "iblai-add-chat.md",
            "iblai-add-component.md",
            "iblai-add-notification.md",
            "iblai-add-profile.md",
            "iblai-add-test.md",
            "iblai-build-windows-msix.md",
            "iblai-iconography.md",
            "iblai-add-shadcn-component.md",
            "iblai-setup.md",
            "iblai-deslop.md",
        }
        actual = {f.name for f in skills_dir.iterdir() if f.suffix == ".md"}
        assert actual == expected

    def test_mcp_generates_opencode_skills(self, generated):
        project, _ = generated
        skills_dir = project.root / ".opencode" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        assert len(skill_dirs) == 13

    def test_mcp_skills_are_symlinked(self, generated):
        """Skills in .claude/, .opencode/, .cursor/ are symlinks to skills/."""
        project, _ = generated
        # Central store exists with categorized subdirs
        skills_dir = project.root / "skills"
        assert skills_dir.is_dir()
        assert (skills_dir / "components" / "iblai-add-auth.md").exists()
        assert (skills_dir / "README.md").exists()

        # Claude symlink (flat)
        claude_link = project.root / ".claude" / "skills" / "iblai-add-auth.md"
        assert claude_link.exists()
        assert claude_link.is_symlink()

        # OpenCode symlink (flat)
        oc_link = project.root / ".opencode" / "skills" / "iblai-add-auth" / "SKILL.md"
        assert oc_link.exists()
        assert oc_link.is_symlink()

        # Cursor symlink (flat)
        cursor_link = project.root / ".cursor" / "rules" / "iblai-add-auth.md"
        assert cursor_link.exists()
        assert cursor_link.is_symlink()


# ---------------------------------------------------------------------------
# src/ directory support
# ---------------------------------------------------------------------------


class TestAddGeneratorsSrcDir:
    """Verify generators respect src/ directory layout."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path, src_dir="src")

    def test_auth_respects_src_dir(self, project):
        from iblai.generators.add_auth import AddAuthGenerator

        created = AddAuthGenerator(project, platform_key="acme").generate()
        assert any("src/lib/iblai/config.ts" in f for f in created)
        assert (project.root / "src" / "lib" / "iblai" / "config.ts").exists()

    def test_chat_respects_src_dir(self, project):
        from iblai.generators.add_chat import AddChatGenerator

        AddChatGenerator(project).generate()
        assert (
            project.root / "src" / "components" / "iblai" / "chat-widget.tsx"
        ).exists()

    def test_profile_respects_src_dir(self, project):
        from iblai.generators.add_profile import AddProfileGenerator

        AddProfileGenerator(project).generate()
        assert (
            project.root / "src" / "components" / "iblai" / "profile-dropdown.tsx"
        ).exists()


# ---------------------------------------------------------------------------
# Auto-apply: next.config, globals.css, .env.local, deps
# ---------------------------------------------------------------------------


class TestAddAuthAutoApply:
    """Verify auth generator patches next.config, globals.css, .env.local, and installs deps."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    @pytest.fixture
    def generated(self, project):
        from iblai.generators.add_auth import AddAuthGenerator

        created = AddAuthGenerator(project, platform_key="acme").generate()
        return project, created

    def test_auth_patches_next_config(self, generated):
        project, _ = generated
        content = (project.root / "next.config.ts").read_text()
        assert "turbopack" in content
        assert "localStorage.getItem" in content
        assert "@tauri-apps/api" not in content

    def test_auth_patches_globals_css(self, generated):
        project, _ = generated
        content = (project.app_dir / "globals.css").read_text()
        assert "iblai-styles.css" in content

    def test_auth_writes_env_local(self, generated):
        project, _ = generated
        content = (project.root / ".env.local").read_text()
        assert "NEXT_PUBLIC_API_BASE_URL" in content
        assert "NEXT_PUBLIC_AUTH_URL" in content
        assert "NEXT_PUBLIC_MAIN_TENANT_KEY=acme" in content

    def test_auth_installs_deps(self, generated, mock_subprocess):
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        # Should be a list starting with the package manager
        assert isinstance(call_args, list)
        assert "add" in call_args

    def test_auth_creates_sdk_symlink(self, generated):
        project, created = generated
        sdk_link = project.lib_dir / "iblai" / "sdk"
        assert sdk_link.is_symlink()
        # Should be a relative symlink targeting node_modules/@iblai/iblai-js/dist
        target = str(sdk_link.readlink())
        assert "node_modules" in target
        assert "@iblai" in target
        assert "iblai-js" in target
        assert "dist" in target
        # Should be relative (not absolute)
        assert not target.startswith("/")

    def test_auth_globals_css_is_clean(self, generated):
        """globals.css must contain only the two import lines, no vanilla boilerplate."""
        project, _ = generated
        content = (project.app_dir / "globals.css").read_text().strip()
        lines = [l for l in content.split("\n") if l.strip()]
        assert len(lines) == 2
        assert "tailwindcss" in lines[0]
        assert "iblai-styles.css" in lines[1]

    def test_auth_generates_tenant_module(self, generated):
        project, _ = generated
        tenant_file = project.lib_dir / "iblai" / "tenant.ts"
        assert tenant_file.exists()
        content = tenant_file.read_text()
        assert "resolveAppTenant" in content
        assert "checkTenantMismatch" in content
        assert "app_tenant" in content
        assert "PLACEHOLDER_TENANTS" in content

    def test_auth_generates_vitest_config(self, generated):
        project, _ = generated
        assert (project.root / "vitest.config.ts").exists()
        content = (project.root / "vitest.config.ts").read_text()
        assert "vitest/config" in content

    def test_auth_generates_source_paths_test(self, generated):
        project, _ = generated
        test_file = project.root / "__tests__" / "source-paths.test.ts"
        assert test_file.exists()
        content = test_file.read_text()
        assert "@source" in content
        assert "lib/iblai/sdk" in content
        assert "web-containers/source" in content


class TestAddChatAutoApply:
    """Verify chat generator installs @iblai/iblai-web-mentor."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    def test_chat_installs_web_mentor(self, project, mock_subprocess):
        from iblai.generators.add_chat import AddChatGenerator

        AddChatGenerator(project).generate()
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        assert "@iblai/iblai-web-mentor" in call_args

    def test_chat_does_not_patch_store(self, project):
        """The web component wrapper does not need Redux store changes."""
        from iblai.generators.add_chat import AddChatGenerator

        store_before = (project.store_dir / "index.ts").read_text()
        AddChatGenerator(project).generate()
        store_after = (project.store_dir / "index.ts").read_text()
        assert store_before == store_after


class TestAddMcpAutoApply:
    """Verify MCP generator installs @iblai/mcp."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_project(tmp_path)

    def test_mcp_installs_dev_dep(self, project, mock_subprocess):
        from iblai.generators.add_mcp import AddMcpGenerator

        AddMcpGenerator(project).generate()
        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        assert "-D" in call_args or "--dev" in call_args


# ---------------------------------------------------------------------------
# Base-template app compatibility (lib/config.ts instead of lib/iblai/config.ts)
# ---------------------------------------------------------------------------


def _make_base_template_project(tmp_path):
    """Create a project that looks like `iblai startapp base` output."""
    root = tmp_path / "base-project"
    root.mkdir()
    (root / "app").mkdir()
    (root / "lib").mkdir()

    pkg = {
        "dependencies": {"next": "15.0.0", "@iblai/iblai-js": "^1.0.33"},
        "devDependencies": {"typescript": "5.0.0"},
    }
    (root / "package.json").write_text(json.dumps(pkg))
    (root / "app" / "globals.css").write_text('@import "tailwindcss";\n')
    (root / "next.config.ts").write_text(
        "const nextConfig = {};\nexport default nextConfig;\n"
    )
    # Base template has lib/config.ts (not lib/iblai/config.ts)
    (root / "lib" / "config.ts").write_text("export const config = {};\n")

    return ProjectInfo(
        root=root,
        framework="nextjs",
        has_app_router=True,
        has_typescript=True,
    )


class TestAddToBaseTemplateApp:
    """Verify iblai add commands work on apps generated by iblai startapp base."""

    @pytest.fixture
    def project(self, tmp_path):
        return _make_base_template_project(tmp_path)

    def test_has_iblai_auth_detects_lib_config(self, project):
        """_has_iblai_auth should return True when lib/config.ts exists."""
        from iblai.commands.add import _has_iblai_auth

        assert _has_iblai_auth(project) is True

    def test_has_iblai_auth_detects_lib_iblai_config(self, tmp_path):
        """_has_iblai_auth should return True when lib/iblai/config.ts exists."""
        from iblai.commands.add import _has_iblai_auth

        proj = _make_project(tmp_path)
        # _make_project doesn't create lib/iblai/config.ts, but it does create lib/config.ts
        # via the next.config.ts. Let's create the iblai variant:
        (proj.lib_dir / "iblai").mkdir(parents=True, exist_ok=True)
        (proj.lib_dir / "iblai" / "config.ts").write_text("export default {};\n")
        assert _has_iblai_auth(proj) is True

    def test_has_iblai_auth_returns_false_when_no_auth(self, tmp_path):
        """_has_iblai_auth should return False when neither config exists."""
        from iblai.commands.add import _has_iblai_auth

        root = tmp_path / "empty"
        root.mkdir()
        (root / "app").mkdir()
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"next": "15.0.0"}})
        )
        proj = ProjectInfo(root=root, framework="nextjs", has_app_router=True)
        assert _has_iblai_auth(proj) is False

    def test_chat_generates_on_base_template(self, project):
        """iblai add chat generators work when lib/config.ts exists."""
        from iblai.generators.add_chat import AddChatGenerator

        created = AddChatGenerator(project).generate()
        assert len(created) == 2
        assert (project.components_dir / "iblai" / "chat-widget.tsx").exists()
        assert (project.root / "types" / "iblai-web-mentor.d.ts").exists()

    def test_profile_generates_on_base_template(self, project):
        from iblai.generators.add_profile import AddProfileGenerator

        created = AddProfileGenerator(project).generate()
        assert len(created) == 1

    def test_notifications_generates_on_base_template(self, project):
        from iblai.generators.add_notifications import AddNotificationsGenerator

        created = AddNotificationsGenerator(project).generate()
        assert len(created) == 1

    def test_account_generates_on_base_template(self, project):
        from iblai.generators.add_account import AddAccountGenerator

        created = AddAccountGenerator(project).generate()
        assert len(created) == 1
        page = project.app_dir / "(app)" / "account" / "page.tsx"
        assert page.exists()
        content = page.read_text()
        assert "Account" in content
        assert "tenants={tenants}" in content
        assert "authURL={config.authUrl()}" in content

    def test_analytics_generates_on_base_template(self, project):
        from iblai.generators.add_analytics import AddAnalyticsGenerator

        created = AddAnalyticsGenerator(project).generate()
        assert len(created) == 1
        page = project.app_dir / "(app)" / "analytics" / "page.tsx"
        assert page.exists()
        content = page.read_text()
        assert "AnalyticsOverview" in content
        assert "tenantKey={tenantKey}" in content
        assert 'mentorId=""' in content


class TestAddTemplatesRender:
    """Verify all add/ templates render through Jinja2 without errors."""

    @pytest.fixture
    def env(self):
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        tpl_dir = Path(__file__).parent.parent / "iblai" / "templates"
        return Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @pytest.fixture
    def add_templates(self, env):
        from pathlib import Path

        tpl_dir = Path(__file__).parent.parent / "iblai" / "templates"
        return sorted(str(f.relative_to(tpl_dir)) for f in tpl_dir.rglob("add/**/*.j2"))

    def test_all_add_templates_render(self, env, add_templates):
        """Every add/ template must render without Jinja2 errors."""
        for tpl_path in add_templates:
            result = env.get_template(tpl_path).render({})
            assert len(result) > 0, f"Template {tpl_path} rendered empty"
