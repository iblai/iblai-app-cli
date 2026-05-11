"""Tests for iblai.commands.deploy mode detection + env push."""

from pathlib import Path
from unittest.mock import patch

import pytest

from iblai.commands.deploy import (
    _detect_deploy_mode,
    _is_placeholder,
    _parse_env_file,
    _project_json_path,
    _push_env_to_vercel,
)


class TestDetectDeployMode:
    """Detect static vs server mode from next.config.{ts,mjs,js}."""

    def test_no_config_defaults_to_server(self, tmp_path):
        assert _detect_deploy_mode(tmp_path) == "server"

    @pytest.mark.parametrize("filename", ["next.config.ts", "next.config.mjs", "next.config.js"])
    def test_output_export_double_quoted(self, tmp_path, filename):
        (tmp_path / filename).write_text(
            'const nextConfig = { output: "export" };\nexport default nextConfig;\n'
        )
        assert _detect_deploy_mode(tmp_path) == "static"

    def test_output_export_single_quoted(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            "const nextConfig = { output: 'export' };\nexport default nextConfig;\n"
        )
        assert _detect_deploy_mode(tmp_path) == "static"

    def test_output_export_whitespace_variations(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'const c = {\n  output:"export",\n};\n'
        )
        assert _detect_deploy_mode(tmp_path) == "static"

    def test_no_output_export_is_server(self, tmp_path):
        (tmp_path / "next.config.ts").write_text(
            'const nextConfig = { images: { remotePatterns: [] } };\n'
            'export default nextConfig;\n'
        )
        assert _detect_deploy_mode(tmp_path) == "server"

    def test_unrelated_output_value_is_server(self, tmp_path):
        # output: "standalone" is server, not static
        (tmp_path / "next.config.ts").write_text(
            'const nextConfig = { output: "standalone" };\n'
        )
        assert _detect_deploy_mode(tmp_path) == "server"

    def test_ts_takes_priority_over_mjs(self, tmp_path):
        # next.config.ts is checked first; static wins over an mjs missing the flag
        (tmp_path / "next.config.ts").write_text(
            'const c = { output: "export" };\n'
        )
        (tmp_path / "next.config.mjs").write_text("export default {};\n")
        assert _detect_deploy_mode(tmp_path) == "static"


class TestProjectJsonPath:
    """Vercel writes .vercel/project.json in different locations per mode."""

    def test_static_mode_uses_out_subdir(self):
        assert _project_json_path("static") == Path("out/.vercel/project.json")

    def test_server_mode_uses_repo_root(self):
        assert _project_json_path("server") == Path(".vercel/project.json")


class TestParseEnvFile:
    """.env.local parser — strips quotes, comments, blanks."""

    def test_missing_file_returns_empty(self, tmp_path):
        assert _parse_env_file(tmp_path / "absent.env") == {}

    def test_simple_pairs(self, tmp_path):
        p = tmp_path / ".env.local"
        p.write_text("KEY=value\nOTHER=foo\n")
        assert _parse_env_file(p) == {"KEY": "value", "OTHER": "foo"}

    def test_strips_double_and_single_quotes(self, tmp_path):
        p = tmp_path / ".env.local"
        p.write_text("A=\"double\"\nB='single'\nC=naked\n")
        assert _parse_env_file(p) == {"A": "double", "B": "single", "C": "naked"}

    def test_skips_comments_and_blanks(self, tmp_path):
        p = tmp_path / ".env.local"
        p.write_text("# a comment\n\nKEY=value\n  # indented comment\n")
        assert _parse_env_file(p) == {"KEY": "value"}

    def test_value_with_equals_sign_preserved(self, tmp_path):
        p = tmp_path / ".env.local"
        p.write_text("URL=https://example.com/?a=1&b=2\n")
        assert _parse_env_file(p) == {"URL": "https://example.com/?a=1&b=2"}

    def test_lines_without_equals_skipped(self, tmp_path):
        p = tmp_path / ".env.local"
        p.write_text("nope\nKEY=value\n")
        assert _parse_env_file(p) == {"KEY": "value"}


class TestIsPlaceholder:
    def test_empty_is_placeholder(self):
        assert _is_placeholder("")

    def test_your_prefix_is_placeholder(self):
        assert _is_placeholder("your-token")
        assert _is_placeholder("your-twenty-api-key")

    def test_real_value_is_not_placeholder(self):
        assert not _is_placeholder("abc123")
        assert not _is_placeholder("https://api.iblai.app")


class TestPushEnvToVercel:
    """Idempotent upsert: POST new, PATCH existing, skip placeholders/reserved."""

    def _existing(self, *keys):
        """Build the GET-existing-envs response Vercel returns."""
        return {"envs": [{"id": f"env_{k}", "key": k, "value": "old"} for k in keys]}

    def test_creates_new_var(self):
        calls = []

        def fake_api(method, path, _token, data=None, team_id=None):
            calls.append((method, path, data))
            if method == "GET":
                return self._existing()
            return {}

        with patch("iblai.commands.deploy._vercel_api", side_effect=fake_api):
            created, updated, skipped = _push_env_to_vercel(
                "tok", "proj_1", None, {"TWENTY_API_KEY": "secret"}
            )

        assert (created, updated, skipped) == (1, 0, 0)
        post_calls = [c for c in calls if c[0] == "POST"]
        assert len(post_calls) == 1
        assert post_calls[0][2]["key"] == "TWENTY_API_KEY"
        assert post_calls[0][2]["type"] == "encrypted"
        assert post_calls[0][2]["target"] == ["production", "preview"]

    def test_updates_existing_var(self):
        calls = []

        def fake_api(method, path, _token, data=None, team_id=None):
            calls.append((method, path, data))
            if method == "GET":
                return self._existing("TWENTY_API_KEY")
            return {}

        with patch("iblai.commands.deploy._vercel_api", side_effect=fake_api):
            created, updated, skipped = _push_env_to_vercel(
                "tok", "proj_1", None, {"TWENTY_API_KEY": "new_value"}
            )

        assert (created, updated, skipped) == (0, 1, 0)
        patch_calls = [c for c in calls if c[0] == "PATCH"]
        assert len(patch_calls) == 1
        assert patch_calls[0][1] == "/v10/projects/proj_1/env/env_TWENTY_API_KEY"
        assert patch_calls[0][2]["value"] == "new_value"

    def test_next_public_uses_plain_type(self):
        captured = {}

        def fake_api(method, path, _token, data=None, team_id=None):
            if method == "GET":
                return self._existing()
            if method == "POST":
                captured["body"] = data
            return {}

        with patch("iblai.commands.deploy._vercel_api", side_effect=fake_api):
            _push_env_to_vercel(
                "tok", "proj_1", None, {"NEXT_PUBLIC_API_BASE_URL": "https://x"}
            )

        assert captured["body"]["type"] == "plain"

    def test_skips_reserved_and_placeholders(self):
        calls = []

        def fake_api(method, path, _token, data=None, team_id=None):
            calls.append(method)
            if method == "GET":
                return self._existing()
            return {}

        env_vars = {
            "TWENTY_API_KEY": "real_value",
            "VERCEL_TOKEN": "secret",           # reserved
            "NODE_ENV": "production",            # reserved
            "PLACEHOLDER": "your-token",         # placeholder
            "EMPTY": "",                         # placeholder
        }
        with patch("iblai.commands.deploy._vercel_api", side_effect=fake_api):
            created, updated, skipped = _push_env_to_vercel(
                "tok", "proj_1", None, env_vars
            )

        assert (created, updated, skipped) == (1, 0, 4)
        # Only 1 POST + 1 GET
        assert calls.count("POST") == 1
        assert calls.count("PATCH") == 0
