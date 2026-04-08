"""Tests for iblai.updater auto-update system."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from iblai.updater import (
    CACHE_TTL,
    _is_newer,
    _parse_version,
    _read_cache,
    _write_cache,
    auto_update,
    check_for_update,
    detect_install_method,
    get_latest_version,
    perform_update,
)


# ---------------------------------------------------------------------------
# detect_install_method
# ---------------------------------------------------------------------------


class TestDetectInstallMethod:
    def test_returns_binary_when_meipass_set(self, monkeypatch):
        monkeypatch.setattr("sys._MEIPASS", "/tmp/frozen", raising=False)
        assert detect_install_method() == "binary"

    def test_returns_npx_when_npx_in_path(self, monkeypatch):
        monkeypatch.delattr("sys._MEIPASS", raising=False)
        monkeypatch.setattr(
            "iblai.updater.__file__",
            "/home/user/.npm/_npx/abc123/node_modules/@iblai/cli/updater.py",
        )
        assert detect_install_method() == "npx"

    def test_returns_npm_when_node_modules_in_path(self, monkeypatch):
        monkeypatch.delattr("sys._MEIPASS", raising=False)
        monkeypatch.setattr(
            "iblai.updater.__file__",
            "/usr/local/lib/node_modules/@iblai/cli-linux-x64/bin/iblai",
        )
        assert detect_install_method() == "npm"

    def test_returns_dev_when_pyproject_and_git_exist(self, monkeypatch, tmp_path):
        monkeypatch.delattr("sys._MEIPASS", raising=False)
        # Create a fake source tree
        pkg_dir = tmp_path / "iblai"
        pkg_dir.mkdir()
        fake_file = pkg_dir / "updater.py"
        fake_file.write_text("")
        (tmp_path / "pyproject.toml").write_text("")
        (tmp_path / ".git").mkdir()
        monkeypatch.setattr("iblai.updater.__file__", str(fake_file))
        assert detect_install_method() == "dev"

    def test_returns_pip_as_default(self, monkeypatch, tmp_path):
        monkeypatch.delattr("sys._MEIPASS", raising=False)
        # No pyproject.toml, no .git, no node_modules
        pkg_dir = tmp_path / "site-packages" / "iblai"
        pkg_dir.mkdir(parents=True)
        fake_file = pkg_dir / "updater.py"
        fake_file.write_text("")
        monkeypatch.setattr("iblai.updater.__file__", str(fake_file))
        assert detect_install_method() == "pip"


# ---------------------------------------------------------------------------
# _parse_version / _is_newer
# ---------------------------------------------------------------------------


class TestParseVersion:
    def test_simple_version(self):
        assert _parse_version("0.2.0") == (0, 2, 0)

    def test_strips_v_prefix(self):
        assert _parse_version("v1.3.0") == (1, 3, 0)

    def test_ignores_prerelease_suffix(self):
        assert _parse_version("0.3.0rc1") == (0, 3, 0)

    def test_single_segment(self):
        assert _parse_version("3") == (3,)


class TestIsNewer:
    def test_newer_minor(self):
        assert _is_newer("0.3.0", "0.2.0")

    def test_newer_patch(self):
        assert _is_newer("0.2.1", "0.2.0")

    def test_same_version(self):
        assert not _is_newer("0.2.0", "0.2.0")

    def test_older_version(self):
        assert not _is_newer("0.1.0", "0.2.0")

    def test_major_bump(self):
        assert _is_newer("1.0.0", "0.9.9")


# ---------------------------------------------------------------------------
# get_latest_version
# ---------------------------------------------------------------------------


class TestGetLatestVersion:
    def test_pip_queries_pypi(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"info": {"version": "0.5.0"}}
        mock_resp.raise_for_status = MagicMock()
        monkeypatch.setattr("iblai.updater.requests.get", lambda *a, **kw: mock_resp)
        assert get_latest_version("pip") == "0.5.0"

    def test_binary_queries_github(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"tag_name": "v0.5.0"}
        mock_resp.raise_for_status = MagicMock()
        monkeypatch.setattr("iblai.updater.requests.get", lambda *a, **kw: mock_resp)
        assert get_latest_version("binary") == "0.5.0"

    def test_returns_none_on_network_error(self, monkeypatch):
        def _raise(*a, **kw):
            raise ConnectionError("no network")

        monkeypatch.setattr("iblai.updater.requests.get", _raise)
        assert get_latest_version("pip") is None


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class TestCache:
    def test_write_and_read_cache(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "update-check.json"
        monkeypatch.setattr("iblai.updater.CACHE_DIR", tmp_path)
        monkeypatch.setattr("iblai.updater.CACHE_FILE", cache_file)

        _write_cache("1.1.0")
        data = _read_cache()
        assert data is not None
        assert data["latest_version"] == "1.1.0"
        assert data["current_version"] == "1.1.0"

    def test_fresh_cache_prevents_network_check(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "update-check.json"
        monkeypatch.setattr("iblai.updater.CACHE_DIR", tmp_path)
        monkeypatch.setattr("iblai.updater.CACHE_FILE", cache_file)

        # Write a fresh cache saying no update
        cache_file.write_text(
            json.dumps(
                {
                    "checked_at": time.time(),
                    "current_version": "1.1.0",
                    "latest_version": "1.1.0",
                }
            )
        )

        # get_latest_version should NOT be called
        called = []
        monkeypatch.setattr(
            "iblai.updater.get_latest_version",
            lambda m: called.append(1) or "9.9.9",
        )
        result = check_for_update("pip")
        assert result is None
        assert len(called) == 0

    def test_stale_cache_triggers_network_check(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "update-check.json"
        monkeypatch.setattr("iblai.updater.CACHE_DIR", tmp_path)
        monkeypatch.setattr("iblai.updater.CACHE_FILE", cache_file)

        # Write a stale cache (25 hours ago)
        cache_file.write_text(
            json.dumps(
                {
                    "checked_at": time.time() - CACHE_TTL - 3600,
                    "current_version": "1.1.0",
                    "latest_version": "1.1.0",
                }
            )
        )

        monkeypatch.setattr("iblai.updater.get_latest_version", lambda m: "1.2.0")
        result = check_for_update("pip")
        assert result == "1.2.0"

    def test_cache_returns_update_when_newer(self, monkeypatch, tmp_path):
        cache_file = tmp_path / "update-check.json"
        monkeypatch.setattr("iblai.updater.CACHE_DIR", tmp_path)
        monkeypatch.setattr("iblai.updater.CACHE_FILE", cache_file)

        cache_file.write_text(
            json.dumps(
                {
                    "checked_at": time.time(),
                    "current_version": "1.1.0",
                    "latest_version": "1.5.0",
                }
            )
        )
        result = check_for_update("pip")
        assert result == "1.5.0"

    def test_read_cache_returns_none_when_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr("iblai.updater.CACHE_FILE", tmp_path / "nonexistent.json")
        assert _read_cache() is None


# ---------------------------------------------------------------------------
# perform_update
# ---------------------------------------------------------------------------


class TestPerformUpdate:
    def test_pip_runs_pip_install(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr("iblai.updater.subprocess.run", mock_run)
        assert perform_update("pip", "0.3.0") is True
        args = mock_run.call_args[0][0]
        assert "-m" in args
        assert "pip" in args
        assert "install" in args
        assert "--upgrade" in args
        assert "iblai-app-cli" in args

    def test_npm_runs_npm_install(self, monkeypatch):
        mock_run = MagicMock(return_value=MagicMock(returncode=0))
        monkeypatch.setattr("iblai.updater.subprocess.run", mock_run)
        assert perform_update("npm", "0.3.0") is True
        args = mock_run.call_args[0][0]
        assert "npm" in args[0] or "npm.cmd" in args[0]
        assert "@iblai/cli@latest" in args

    def test_dev_returns_false(self):
        assert perform_update("dev", "0.3.0") is False

    def test_pip_with_permission_error_asks_sudo(self, monkeypatch):
        # First call fails with permission error
        fail_result = MagicMock(returncode=1, stderr="Permission denied")
        success_result = MagicMock(returncode=0)
        call_count = [0]

        def mock_run(cmd, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return fail_result
            return success_result

        monkeypatch.setattr("iblai.updater.subprocess.run", mock_run)
        monkeypatch.setattr("iblai.updater.shutil.which", lambda c: "/usr/bin/sudo")
        monkeypatch.setattr("iblai.updater.click.confirm", lambda *a, **kw: True)
        assert perform_update("pip", "0.3.0") is True
        assert call_count[0] == 2  # First attempt + sudo attempt

    def test_pip_user_declines_sudo(self, monkeypatch):
        fail_result = MagicMock(returncode=1, stderr="Permission denied")
        monkeypatch.setattr(
            "iblai.updater.subprocess.run",
            MagicMock(return_value=fail_result),
        )
        monkeypatch.setattr("iblai.updater.shutil.which", lambda c: "/usr/bin/sudo")
        monkeypatch.setattr("iblai.updater.click.confirm", lambda *a, **kw: False)
        assert perform_update("pip", "0.3.0") is False


# ---------------------------------------------------------------------------
# auto_update
# ---------------------------------------------------------------------------


class TestAutoUpdate:
    def test_skips_dev_installs(self, monkeypatch):
        monkeypatch.setattr("iblai.updater.detect_install_method", lambda: "dev")
        called = []
        monkeypatch.setattr(
            "iblai.updater.check_for_update",
            lambda m: called.append(1) or "9.9.9",
        )
        auto_update()
        assert len(called) == 0

    def test_skips_npx(self, monkeypatch):
        monkeypatch.setattr("iblai.updater.detect_install_method", lambda: "npx")
        called = []
        monkeypatch.setattr(
            "iblai.updater.check_for_update",
            lambda m: called.append(1) or "9.9.9",
        )
        auto_update()
        assert len(called) == 0

    def test_does_nothing_when_up_to_date(self, monkeypatch, capsys):
        monkeypatch.setattr("iblai.updater.detect_install_method", lambda: "pip")
        monkeypatch.setattr("iblai.updater.check_for_update", lambda m: None)
        auto_update()
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_prints_update_message_to_stderr(self, monkeypatch, capsys):
        monkeypatch.setattr("iblai.updater.detect_install_method", lambda: "pip")
        monkeypatch.setattr("iblai.updater.check_for_update", lambda m: "0.9.0")
        monkeypatch.setattr("iblai.updater.perform_update", lambda m, v: True)
        monkeypatch.setattr("iblai.updater._write_cache", lambda v: None)
        auto_update()
        captured = capsys.readouterr()
        assert "0.9.0" in captured.err
        assert "Updated" in captured.err

    def test_never_raises(self, monkeypatch):
        def _boom():
            raise RuntimeError("kaboom")

        monkeypatch.setattr("iblai.updater.detect_install_method", _boom)
        # Must not raise
        auto_update()
