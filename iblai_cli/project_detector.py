"""Detect project type and structure for the `iblai add` command."""

import json
from pathlib import Path
from typing import Optional


class ProjectInfo:
    """Information about a detected project."""

    def __init__(
        self,
        root: Path,
        framework: str,
        has_app_router: bool = False,
        has_pages_router: bool = False,
        has_redux: bool = False,
        has_iblai: bool = False,
        has_typescript: bool = False,
        src_dir: Optional[str] = None,
    ):
        self.root = root
        self.framework = framework  # "nextjs", "unknown"
        self.has_app_router = has_app_router
        self.has_pages_router = has_pages_router
        self.has_redux = has_redux
        self.has_iblai = has_iblai
        self.has_typescript = has_typescript
        self.src_dir = src_dir  # "src" or None

    @property
    def app_dir(self) -> Path:
        """Return the app directory path (src/app or app)."""
        if self.src_dir:
            return self.root / self.src_dir / "app"
        return self.root / "app"

    @property
    def components_dir(self) -> Path:
        """Return the components directory path."""
        if self.src_dir:
            return self.root / self.src_dir / "components"
        return self.root / "components"

    @property
    def lib_dir(self) -> Path:
        """Return the lib directory path."""
        if self.src_dir:
            return self.root / self.src_dir / "lib"
        return self.root / "lib"

    @property
    def store_dir(self) -> Path:
        """Return the store directory path."""
        if self.src_dir:
            return self.root / self.src_dir / "store"
        return self.root / "store"

    @property
    def providers_dir(self) -> Path:
        """Return the providers directory path."""
        if self.src_dir:
            return self.root / self.src_dir / "providers"
        return self.root / "providers"


def detect_project(project_dir: str = ".") -> Optional[ProjectInfo]:
    """
    Detect the project type by examining package.json and directory structure.

    Args:
        project_dir: Path to the project directory.

    Returns:
        ProjectInfo if a supported project is detected, None otherwise.
    """
    root = Path(project_dir).resolve()
    pkg_json_path = root / "package.json"

    if not pkg_json_path.exists():
        return None

    try:
        with open(pkg_json_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

    # Detect framework
    if "next" not in all_deps:
        return ProjectInfo(root=root, framework="unknown")

    # Detect src directory
    src_dir = None
    if (root / "src" / "app").is_dir() or (root / "src" / "pages").is_dir():
        src_dir = "src"

    # Detect App Router vs Pages Router
    has_app_router = (root / "app").is_dir() or (root / "src" / "app").is_dir()
    has_pages_router = (root / "pages").is_dir() or (root / "src" / "pages").is_dir()

    # Detect existing integrations
    has_redux = "@reduxjs/toolkit" in all_deps
    has_iblai = "@iblai/iblai-js" in all_deps
    has_typescript = "typescript" in all_deps

    return ProjectInfo(
        root=root,
        framework="nextjs",
        has_app_router=has_app_router,
        has_pages_router=has_pages_router,
        has_redux=has_redux,
        has_iblai=has_iblai,
        has_typescript=has_typescript,
        src_dir=src_dir,
    )
