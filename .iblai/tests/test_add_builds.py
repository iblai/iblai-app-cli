"""Tests for the AddBuildsGenerator."""

import json

import pytest


class TestAddBuildsGenerator:
    """Tests for adding Tauri v2 desktop shell to a project."""

    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a minimal Next.js project to add Tauri to."""
        pkg = {
            "name": "test-app",
            "version": "0.1.0",
            "scripts": {"dev": "next dev", "build": "next build"},
            "dependencies": {"next": "^16.2.1", "react": "^19.2.4"},
            "devDependencies": {},
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg, indent=2))

        # Create a next.config.ts (like generated apps have)
        (tmp_path / "next.config.ts").write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  turbopack: {},\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n"
            "export default nextConfig;\n"
        )
        return tmp_path

    @pytest.fixture
    def generated_dir(self, project_dir):
        """Run AddBuildsGenerator on the project."""
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(project_dir))
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

    def test_tauri_conf_identifier_has_no_underscores(self, generated_dir):
        data = json.loads((generated_dir / "src-tauri" / "tauri.conf.json").read_text())
        identifier = data["identifier"]
        assert "_" not in identifier, f"Identifier '{identifier}' contains underscores"
        assert identifier == "com.test.app.application"

    def test_appx_manifest_name_has_no_underscores(self, generated_dir):
        content = (generated_dir / "src-tauri" / "AppxManifest.xml").read_text()
        # Extract Name="..." from Identity element
        import re

        match = re.search(r'Name="([^"]+)"', content)
        assert match, "No Name attribute found in AppxManifest.xml"
        name = match.group(1)
        assert "_" not in name, f"Name '{name}' contains underscores"
        assert name == "com.test.app.application"

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

    def test_generates_icon_files(self, generated_dir):
        icons_dir = generated_dir / "src-tauri" / "icons"
        assert icons_dir.is_dir()
        for name in [
            "icon.ico",
            "icon.icns",
            "icon.png",
            "32x32.png",
            "128x128.png",
            "128x128@2x.png",
        ]:
            icon = icons_dir / name
            assert icon.exists(), f"Missing icon: {name}"
            assert icon.stat().st_size > 0, f"Empty icon: {name}"

    def test_generates_msix_icon_files(self, generated_dir):
        icons_dir = generated_dir / "src-tauri" / "icons"
        for name in [
            "StoreLogo.png",
            "Square44x44Logo.png",
            "Square71x71Logo.png",
            "Square150x150Logo.png",
            "Square310x310Logo.png",
            "Wide310x150Logo.png",
        ]:
            icon = icons_dir / name
            assert icon.exists(), f"Missing MSIX icon: {name}"

    def test_icon_png_is_valid_rgba(self, generated_dir):
        """Icon PNGs are valid RGBA format."""
        png = (generated_dir / "src-tauri" / "icons" / "icon.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        # Color type is at byte offset 25 in IHDR chunk: 6 = RGBA
        assert png[25] == 6, f"Expected RGBA (color type 6), got {png[25]}"

    def test_icon_ico_is_valid(self, generated_dir):
        """Placeholder ICO starts with the correct ICO signature."""
        ico = (generated_dir / "src-tauri" / "icons" / "icon.ico").read_bytes()
        # ICO header: reserved=0, type=1 (icon)
        assert ico[:4] == b"\x00\x00\x01\x00"

    def test_icon_icns_is_valid(self, generated_dir):
        """Placeholder ICNS starts with the correct magic bytes."""
        icns = (generated_dir / "src-tauri" / "icons" / "icon.icns").read_bytes()
        assert icns[:4] == b"icns"

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
        assert "https://*.iblai.app/*" in urls

    def test_generates_appx_manifest(self, generated_dir):
        manifest = generated_dir / "src-tauri" / "AppxManifest.xml"
        assert manifest.exists()
        content = manifest.read_text()
        assert "test-app" in content
        assert "internetClient" in content
        assert "ProcessorArchitecture" in content
        assert 'Publisher="CN=test-app-dev"' in content

    def test_generates_setup_test_cert_script(self, generated_dir):
        script = generated_dir / "src-tauri" / "setup-test-cert.ps1"
        assert script.exists()
        content = script.read_text()
        assert "New-SelfSignedCertificate" in content
        assert "test-app-dev" in content
        assert "Administrator" in content
        assert '"Root"' in content
        assert '"TrustedPeople"' in content
        assert '"LocalMachine"' in content
        assert "exit 1" in content

    def test_generates_build_msix_script(self, generated_dir):
        script = generated_dir / "src-tauri" / "build-msix.ps1"
        assert script.exists()
        content = script.read_text()
        assert "makeappx" in content.lower() or "MakeAppx" in content
        assert "test-app" in content  # Binary name uses hyphens (from [[bin]] name)
        assert "-Architecture" in content

    def test_patches_package_json_adds_msix_scripts(self, generated_dir):
        data = json.loads((generated_dir / "package.json").read_text())
        assert "tauri:build:msix" in data["scripts"]
        assert "tauri:build:msix:arm64" in data["scripts"]
        assert "build-msix.ps1" in data["scripts"]["tauri:build:msix"]
        assert "arm64" in data["scripts"]["tauri:build:msix:arm64"]
        assert "tauri:setup:cert" in data["scripts"]
        assert "setup-test-cert.ps1" in data["scripts"]["tauri:setup:cert"]

    def test_patches_package_json_adds_ios_scripts(self, generated_dir):
        data = json.loads((generated_dir / "package.json").read_text())
        assert "tauri:dev:ios" in data["scripts"]
        assert "tauri:build:ios" in data["scripts"]
        assert data["scripts"]["tauri:dev:ios"] == "tauri ios dev"
        assert data["scripts"]["tauri:build:ios"] == "tauri ios build"

    def test_next_config_has_no_tauri_stubs(self, generated_dir):
        content = (generated_dir / "next.config.ts").read_text()
        assert '@tauri-apps/api/core"] = false' not in content
        assert '@tauri-apps/api/event"] = false' not in content
        assert "tauri-stub" not in content

    def test_patches_next_config_adds_static_export(self, generated_dir):
        content = (generated_dir / "next.config.ts").read_text()
        assert 'output: "export"' in content
        assert "unoptimized: true" in content

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
        assert data["scripts"]["tauri:dev"] == "tauri dev"

    def test_idempotent_package_json_patching(self, generated_dir):
        """Running generate twice doesn't duplicate entries."""
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(generated_dir))
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
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(project_dir))
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
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=False, ios=True)
        assert ".github/workflows/tauri-build-ios.yml" in created
        wf = project_dir / ".github" / "workflows" / "tauri-build-ios.yml"
        assert wf.exists()
        content = wf.read_text()
        assert "cargo tauri ios build" in content
        assert "aarch64-apple-ios" in content

    def test_generates_windows_msix_workflow(self, project_dir):
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=False, ios=False, windows_msix=True)
        assert ".github/workflows/tauri-build-windows-msix.yml" in created
        wf = project_dir / ".github" / "workflows" / "tauri-build-windows-msix.yml"
        assert wf.exists()
        content = wf.read_text()
        assert "windows-latest" in content
        assert "windows-11-arm" in content
        assert "msixbundle" in content
        assert "build-msix.ps1" in content

    def test_generates_all_workflows(self, project_dir):
        from iblai.generators.add_builds import AddBuildsGenerator

        gen = AddBuildsGenerator(project_root=str(project_dir))
        created = gen.generate_ci_workflows(desktop=True, ios=True, windows_msix=True)
        assert len(created) == 3


class TestNextConfigTauriPatching:
    """Tests for patch_next_config_for_tauri()."""

    def test_adds_export_to_config(self, tmp_path):
        from iblai.next_config_patcher import patch_next_config_for_tauri

        config = tmp_path / "next.config.ts"
        config.write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "  turbopack: {},\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n"
            "export default nextConfig;\n"
        )
        result = patch_next_config_for_tauri(tmp_path)
        assert result is not None
        content = config.read_text()
        assert 'output: "export"' in content
        assert "tauri-stub" not in content

    def test_idempotent_patching(self, tmp_path):
        from iblai.next_config_patcher import patch_next_config_for_tauri

        config = tmp_path / "next.config.ts"
        config.write_text(
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            '  output: "export",\n'
            "};\n"
            "export default nextConfig;\n"
        )
        result = patch_next_config_for_tauri(tmp_path)
        # Already patched — no changes
        assert result is None

    def test_returns_none_when_no_config(self, tmp_path):
        from iblai.next_config_patcher import patch_next_config_for_tauri

        result = patch_next_config_for_tauri(tmp_path)
        assert result is None
