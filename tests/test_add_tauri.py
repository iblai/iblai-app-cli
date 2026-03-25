"""Tests for the AddTauriGenerator."""

import json

import pytest


class TestAddTauriGenerator:
    """Tests for adding Tauri v2 desktop shell to a project."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a minimal Next.js project to add Tauri to."""
        pkg = {
            "name": "test-app",
            "version": "0.1.0",
            "scripts": {"dev": "next dev", "build": "next build"},
            "dependencies": {"next": "15.5.14", "react": "19.1.0"},
            "devDependencies": {},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg, indent=2))

        # Create a next.config.mjs with Tauri stubs (like generated apps have)
        (tmp_path / "next.config.mjs").write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  webpack: (config) => {\n"
            "    // Stub out @tauri-apps/api imports\n"
            '    config.resolve.alias["@tauri-apps/api/core"] = false;\n'
            '    config.resolve.alias["@tauri-apps/api/event"] = false;\n'
            "    return config;\n"
            "  },\n"
            "};\n"
            "export default nextConfig;\n"
        )
        return tmp_path

    @pytest.fixture
    def generated_dir(self, project_dir):
        """Run AddTauriGenerator on the project."""
        from iblai_cli.generators.add_tauri import AddTauriGenerator

        gen = AddTauriGenerator(project_root=str(project_dir))
        gen.generate()
        return project_dir

    def test_generates_src_tauri_directory(self, generated_dir):
        assert (generated_dir / "src-tauri").is_dir()

    def test_generates_tauri_conf_json(self, generated_dir):
        conf = generated_dir / "src-tauri" / "tauri.conf.json"
        assert conf.exists()
        data = json.loads(conf.read_text())
        assert isinstance(data, dict)
        assert data["$schema"] == "https://schema.tauri.app/config/2.0.0"

    def test_tauri_conf_has_correct_product_name(self, generated_dir):
        data = json.loads((generated_dir / "src-tauri" / "tauri.conf.json").read_text())
        assert data["productName"] == "test-app"

    def test_tauri_conf_has_dev_url(self, generated_dir):
        data = json.loads((generated_dir / "src-tauri" / "tauri.conf.json").read_text())
        assert data["build"]["devUrl"] == "http://localhost:3000"

    def test_tauri_conf_has_frontend_dist(self, generated_dir):
        data = json.loads((generated_dir / "src-tauri" / "tauri.conf.json").read_text())
        assert data["build"]["frontendDist"] == "../out"

    def test_generates_cargo_toml(self, generated_dir):
        cargo = generated_dir / "src-tauri" / "Cargo.toml"
        assert cargo.exists()
        content = cargo.read_text()
        assert "tauri" in content
        assert "tauri-plugin-opener" in content

    def test_generates_build_rs(self, generated_dir):
        build_rs = generated_dir / "src-tauri" / "build.rs"
        assert build_rs.exists()
        assert "tauri_build::build()" in build_rs.read_text()

    def test_generates_main_rs(self, generated_dir):
        main_rs = generated_dir / "src-tauri" / "src" / "main.rs"
        assert main_rs.exists()
        content = main_rs.read_text()
        assert "fn main()" in content
        assert "windows_subsystem" in content

    def test_generates_lib_rs(self, generated_dir):
        lib_rs = generated_dir / "src-tauri" / "src" / "lib.rs"
        assert lib_rs.exists()
        content = lib_rs.read_text()
        assert "pub fn run()" in content
        assert "tauri::Builder" in content

    def test_generates_capabilities_default_json(self, generated_dir):
        cap = generated_dir / "src-tauri" / "capabilities" / "default.json"
        assert cap.exists()
        data = json.loads(cap.read_text())
        assert data["identifier"] == "default"

    def test_capabilities_has_iblai_remote_urls(self, generated_dir):
        data = json.loads(
            (generated_dir / "src-tauri" / "capabilities" / "default.json").read_text()
        )
        urls = data["remote"]["urls"]
        assert "https://*.iblai.app/*" in urls
        assert "https://*.iblai.org/*" in urls

    def test_patches_next_config_removes_tauri_stubs(self, generated_dir):
        content = (generated_dir / "next.config.mjs").read_text()
        assert '@tauri-apps/api/core"] = false' not in content
        assert '@tauri-apps/api/event"] = false' not in content

    def test_patches_next_config_adds_conditional_export(self, generated_dir):
        content = (generated_dir / "next.config.mjs").read_text()
        assert "TAURI_ENV_PLATFORM" in content
        assert "output:" in content

    def test_patches_package_json_adds_tauri_api(self, generated_dir):
        data = json.loads((generated_dir / "package.json").read_text())
        assert "@tauri-apps/api" in data["dependencies"]

    def test_patches_package_json_adds_tauri_cli_dev(self, generated_dir):
        data = json.loads((generated_dir / "package.json").read_text())
        assert "@tauri-apps/cli" in data["devDependencies"]

    def test_patches_package_json_adds_tauri_scripts(self, generated_dir):
        data = json.loads((generated_dir / "package.json").read_text())
        assert "tauri:dev" in data["scripts"]
        assert "tauri:build" in data["scripts"]
        assert data["scripts"]["tauri:dev"] == "cargo tauri dev"

    def test_idempotent_package_json_patching(self, generated_dir):
        """Running generate twice doesn't duplicate entries."""
        from iblai_cli.generators.add_tauri import AddTauriGenerator

        gen = AddTauriGenerator(project_root=str(generated_dir))
        gen._patch_package_json()
        data = json.loads((generated_dir / "package.json").read_text())
        # Should still have exactly one @tauri-apps/api entry
        assert data["dependencies"]["@tauri-apps/api"] == "^2.9.1"


class TestTauriCIWorkflows:
    """Tests for CI workflow generation."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        pkg = {"name": "test-app", "version": "0.1.0"}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        return tmp_path

    def test_generates_desktop_workflow(self, project_dir):
        from iblai_cli.generators.add_tauri import AddTauriGenerator

        gen = AddTauriGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=True, ios=False)
        assert ".github/workflows/tauri-build-desktop.yml" in created
        wf = project_dir / ".github" / "workflows" / "tauri-build-desktop.yml"
        assert wf.exists()
        content = wf.read_text()
        assert "cargo tauri build" in content
        assert "macos-latest" in content
        assert "ubuntu-latest" in content
        assert "windows-latest" in content

    def test_generates_ios_workflow(self, project_dir):
        from iblai_cli.generators.add_tauri import AddTauriGenerator

        gen = AddTauriGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=False, ios=True)
        assert ".github/workflows/tauri-build-ios.yml" in created
        wf = project_dir / ".github" / "workflows" / "tauri-build-ios.yml"
        assert wf.exists()
        content = wf.read_text()
        assert "cargo tauri ios build" in content
        assert "aarch64-apple-ios" in content

    def test_generates_all_workflows(self, project_dir):
        from iblai_cli.generators.add_tauri import AddTauriGenerator

        gen = AddTauriGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=True, ios=True)
        assert len(created) == 2


class TestNextConfigTauriPatching:
    """Tests for patch_next_config_for_tauri()."""

    def test_removes_stubs_from_mjs(self, tmp_path):
        from iblai_cli.next_config_patcher import patch_next_config_for_tauri

        config = tmp_path / "next.config.mjs"
        config.write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  webpack: (config) => {\n"
            '    config.resolve.alias["@tauri-apps/api/core"] = false;\n'
            '    config.resolve.alias["@tauri-apps/api/event"] = false;\n'
            "    return config;\n"
            "  },\n"
            "};\n"
            "export default nextConfig;\n"
        )
        result = patch_next_config_for_tauri(tmp_path)
        assert result is not None
        content = config.read_text()
        assert '@tauri-apps/api/core"] = false' not in content
        assert "TAURI_ENV_PLATFORM" in content

    def test_idempotent_patching(self, tmp_path):
        from iblai_cli.next_config_patcher import patch_next_config_for_tauri

        config = tmp_path / "next.config.mjs"
        config.write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            '  output: process.env.TAURI_ENV_PLATFORM ? "export" : undefined,\n'
            "};\n"
            "export default nextConfig;\n"
        )
        result = patch_next_config_for_tauri(tmp_path)
        # Already patched — no changes
        assert result is None

    def test_returns_none_when_no_config(self, tmp_path):
        from iblai_cli.next_config_patcher import patch_next_config_for_tauri

        result = patch_next_config_for_tauri(tmp_path)
        assert result is None
