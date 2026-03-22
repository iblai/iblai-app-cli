"""Tests for iblai_cli.next_config_patcher -- next.config, globals.css, .env.local patching."""

import pytest

from iblai_cli.next_config_patcher import (
    find_next_config,
    patch_next_config,
    patch_globals_css,
    write_env_local,
)


class TestFindNextConfig:
    """Tests for find_next_config()."""

    def test_finds_next_config_ts(self, tmp_path):
        (tmp_path / "next.config.ts").write_text("export default {};")
        assert find_next_config(tmp_path) == tmp_path / "next.config.ts"

    def test_finds_next_config_mjs(self, tmp_path):
        (tmp_path / "next.config.mjs").write_text("export default {};")
        assert find_next_config(tmp_path) == tmp_path / "next.config.mjs"

    def test_finds_next_config_js(self, tmp_path):
        (tmp_path / "next.config.js").write_text("module.exports = {};")
        assert find_next_config(tmp_path) == tmp_path / "next.config.js"

    def test_ts_takes_precedence_over_mjs(self, tmp_path):
        (tmp_path / "next.config.ts").write_text("")
        (tmp_path / "next.config.mjs").write_text("")
        assert find_next_config(tmp_path) == tmp_path / "next.config.ts"

    def test_returns_none_when_no_config(self, tmp_path):
        assert find_next_config(tmp_path) is None


class TestPatchNextConfig:
    """Tests for patch_next_config()."""

    def test_creates_next_config_ts_when_missing(self, tmp_path):
        result = patch_next_config(tmp_path)
        assert result == "next.config.ts"
        content = (tmp_path / "next.config.ts").read_text()
        assert "localStorage.getItem" in content
        assert "@tauri-apps/api/core" in content
        assert "NextConfig" in content
        assert "export default nextConfig" in content

    def test_patches_existing_ts_adds_polyfill(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'import type { NextConfig } from "next";\n\n'
            "const nextConfig: NextConfig = {\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n\n"
            "export default nextConfig;\n"
        )
        patch_next_config(tmp_path)
        content = (tmp_path / "next.config.ts").read_text()
        assert "localStorage.getItem" in content
        # Polyfill should be before the import
        polyfill_pos = content.index("localStorage.getItem")
        import_pos = content.index("import type")
        assert polyfill_pos < import_pos

    def test_patches_existing_ts_adds_tauri_stubs(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'import type { NextConfig } from "next";\n\n'
            "const nextConfig: NextConfig = {\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n\n"
            "export default nextConfig;\n"
        )
        patch_next_config(tmp_path)
        content = (tmp_path / "next.config.ts").read_text()
        assert "@tauri-apps/api/core" in content
        assert "@tauri-apps/api/event" in content

    def test_patches_mjs_with_js_polyfill(self, tmp_path):
        (tmp_path / "next.config.mjs").write_text(
            "/** @type {import('next').NextConfig} */\n"
            "const nextConfig = {\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n\n"
            "export default nextConfig;\n"
        )
        patch_next_config(tmp_path)
        content = (tmp_path / "next.config.mjs").read_text()
        assert "localStorage.getItem" in content
        # .mjs should NOT have TypeScript type annotations
        assert "Record<string, string>" not in content

    def test_patch_is_idempotent(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'import type { NextConfig } from "next";\n\n'
            "const nextConfig: NextConfig = {\n"
            "  webpack: (config) => {\n"
            "    return config;\n"
            "  },\n"
            "};\n\n"
            "export default nextConfig;\n"
        )
        patch_next_config(tmp_path)
        first_content = (tmp_path / "next.config.ts").read_text()
        patch_next_config(tmp_path)
        second_content = (tmp_path / "next.config.ts").read_text()
        assert first_content == second_content

    def test_adds_webpack_to_config_without_one(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'import type { NextConfig } from "next";\n\n'
            "const nextConfig: NextConfig = {\n"
            "  reactStrictMode: true,\n"
            "};\n\n"
            "export default nextConfig;\n"
        )
        patch_next_config(tmp_path)
        content = (tmp_path / "next.config.ts").read_text()
        assert "@tauri-apps/api/core" in content
        assert "webpack" in content


class TestPatchGlobalsCss:
    """Tests for patch_globals_css()."""

    def test_adds_import_to_globals_css(self, tmp_path):
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "globals.css").write_text('@import "tailwindcss";\n')
        result = patch_globals_css(tmp_path, app_dir)
        assert result is not None
        content = (app_dir / "globals.css").read_text()
        assert "@import './iblai-styles.css';" in content

    def test_import_placed_after_existing_imports(self, tmp_path):
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "globals.css").write_text(
            '@import "tailwindcss";\n@import "other.css";\n\nbody { margin: 0; }\n'
        )
        patch_globals_css(tmp_path, app_dir)
        content = (app_dir / "globals.css").read_text()
        lines = content.split("\n")
        import_idx = next(i for i, l in enumerate(lines) if "iblai-styles" in l)
        # Should be after the last @import line (index 1)
        assert import_idx == 2

    def test_idempotent(self, tmp_path):
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "globals.css").write_text('@import "tailwindcss";\n')
        patch_globals_css(tmp_path, app_dir)
        first = (app_dir / "globals.css").read_text()
        patch_globals_css(tmp_path, app_dir)
        second = (app_dir / "globals.css").read_text()
        assert first == second

    def test_returns_none_when_no_css(self, tmp_path):
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        assert patch_globals_css(tmp_path, app_dir) is None


class TestWriteEnvLocal:
    """Tests for write_env_local()."""

    def test_creates_new_env_local(self, tmp_path):
        write_env_local(tmp_path, {"NEXT_PUBLIC_AUTH_URL": "https://auth.iblai.org"})
        content = (tmp_path / ".env.local").read_text()
        assert "NEXT_PUBLIC_AUTH_URL=https://auth.iblai.org" in content
        assert "# IBL.ai Configuration" in content

    def test_appends_to_existing(self, tmp_path):
        (tmp_path / ".env.local").write_text("EXISTING_VAR=hello\n")
        write_env_local(tmp_path, {"NEW_VAR": "world"})
        content = (tmp_path / ".env.local").read_text()
        assert "EXISTING_VAR=hello" in content
        assert "NEW_VAR=world" in content

    def test_does_not_duplicate_keys(self, tmp_path):
        (tmp_path / ".env.local").write_text("NEXT_PUBLIC_AUTH_URL=existing\n")
        write_env_local(tmp_path, {"NEXT_PUBLIC_AUTH_URL": "new-value"})
        content = (tmp_path / ".env.local").read_text()
        assert content.count("NEXT_PUBLIC_AUTH_URL") == 1
        assert "NEXT_PUBLIC_AUTH_URL=existing" in content

    def test_mixed_new_and_existing(self, tmp_path):
        (tmp_path / ".env.local").write_text("KEY_A=old\n")
        write_env_local(tmp_path, {"KEY_A": "new", "KEY_B": "val"})
        content = (tmp_path / ".env.local").read_text()
        assert content.count("KEY_A") == 1
        assert "KEY_B=val" in content
