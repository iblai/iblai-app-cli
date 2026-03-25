"""Tests for iblai_cli.project_detector -- Next.js project detection."""

import json

import pytest

from iblai_cli.project_detector import ProjectInfo, detect_project


def _write_pkg(tmp_path, deps=None, dev_deps=None):
    """Helper: write a package.json with given deps."""
    pkg = {}
    if deps:
        pkg["dependencies"] = deps
    if dev_deps:
        pkg["devDependencies"] = dev_deps
    (tmp_path / "package.json").write_text(json.dumps(pkg))


class TestDetectProject:
    """Tests for detect_project()."""

    def test_no_package_json_returns_none(self, tmp_path):
        assert detect_project(str(tmp_path)) is None

    def test_invalid_json_returns_none(self, tmp_path):
        (tmp_path / "package.json").write_text("not json{{{")
        assert detect_project(str(tmp_path)) is None

    def test_non_nextjs_returns_unknown(self, tmp_path):
        _write_pkg(tmp_path, deps={"react": "19.0.0"})
        result = detect_project(str(tmp_path))
        assert result is not None
        assert result.framework == "unknown"

    def test_nextjs_app_router_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0"})
        (tmp_path / "app").mkdir()
        result = detect_project(str(tmp_path))
        assert result.framework == "nextjs"
        assert result.has_app_router is True
        assert result.has_pages_router is False

    def test_nextjs_pages_router_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0"})
        (tmp_path / "pages").mkdir()
        result = detect_project(str(tmp_path))
        assert result.framework == "nextjs"
        assert result.has_pages_router is True

    def test_src_dir_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0"})
        (tmp_path / "src" / "app").mkdir(parents=True)
        result = detect_project(str(tmp_path))
        assert result.src_dir == "src"
        assert result.has_app_router is True

    def test_typescript_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0"}, dev_deps={"typescript": "5.0.0"})
        result = detect_project(str(tmp_path))
        assert result.has_typescript is True

    def test_redux_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0", "@reduxjs/toolkit": "2.0.0"})
        result = detect_project(str(tmp_path))
        assert result.has_redux is True

    def test_iblai_detected(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0", "@iblai/iblai-js": "1.0.0"})
        result = detect_project(str(tmp_path))
        assert result.has_iblai is True

    def test_no_src_dir(self, tmp_path):
        _write_pkg(tmp_path, deps={"next": "15.0.0"})
        (tmp_path / "app").mkdir()
        result = detect_project(str(tmp_path))
        assert result.src_dir is None


class TestProjectInfoProperties:
    """Tests for ProjectInfo path properties."""

    def test_paths_without_src(self, tmp_path):
        info = ProjectInfo(root=tmp_path, framework="nextjs")
        assert info.app_dir == tmp_path / "app"
        assert info.components_dir == tmp_path / "components"
        assert info.lib_dir == tmp_path / "lib"
        assert info.store_dir == tmp_path / "store"
        assert info.providers_dir == tmp_path / "providers"

    def test_paths_with_src(self, tmp_path):
        info = ProjectInfo(root=tmp_path, framework="nextjs", src_dir="src")
        assert info.app_dir == tmp_path / "src" / "app"
        assert info.components_dir == tmp_path / "src" / "components"
        assert info.lib_dir == tmp_path / "src" / "lib"
        assert info.store_dir == tmp_path / "src" / "store"
        assert info.providers_dir == tmp_path / "src" / "providers"
