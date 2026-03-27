"""Tests for iblai.package_manager -- package manager detection."""

import json

import pytest

from iblai.package_manager import detect_package_manager, _already_installed


class TestDetectPackageManager:
    """Tests for detect_package_manager()."""

    def test_detect_pnpm_from_lockfile(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "pnpm-lock.yaml").write_text("")
        assert detect_package_manager(tmp_path) == "pnpm"

    def test_detect_yarn_from_lockfile(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "yarn.lock").write_text("")
        assert detect_package_manager(tmp_path) == "yarn"

    def test_detect_bun_from_lockfile(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "bun.lock").write_text("")
        assert detect_package_manager(tmp_path) == "bun"

    def test_detect_bun_from_lockb(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "bun.lockb").write_text("")
        assert detect_package_manager(tmp_path) == "bun"

    def test_detect_npm_default(self, tmp_path):
        (tmp_path / "package.json").write_text("{}")
        assert detect_package_manager(tmp_path) == "npm"

    def test_detect_from_packageManager_field_pnpm(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"packageManager": "pnpm@9.0.0"})
        )
        assert detect_package_manager(tmp_path) == "pnpm"

    def test_detect_from_packageManager_field_yarn(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"packageManager": "yarn@4.0.0"})
        )
        assert detect_package_manager(tmp_path) == "yarn"

    def test_lockfile_takes_precedence_over_field(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"packageManager": "yarn@4.0.0"})
        )
        (tmp_path / "pnpm-lock.yaml").write_text("")
        assert detect_package_manager(tmp_path) == "pnpm"


class TestAlreadyInstalled:
    """Tests for _already_installed() filtering."""

    def test_filters_existing_deps(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"dependencies": {"react": "19.0.0", "next": "15.0.0"}})
        )
        result = _already_installed(tmp_path, ["react", "vue", "next"])
        assert result == ["vue"]

    def test_checks_dev_deps_too(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"devDependencies": {"typescript": "5.0.0"}})
        )
        result = _already_installed(tmp_path, ["typescript", "eslint"])
        assert result == ["eslint"]

    def test_returns_all_when_no_package_json(self, tmp_path):
        result = _already_installed(tmp_path, ["react", "next"])
        assert result == ["react", "next"]
