"""Detect and invoke the project's Node.js package manager."""

import json
import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console

console = Console()


def detect_package_manager(root: Path) -> str:
    """
    Detect the package manager by lockfile or packageManager field.

    Resolution order: pnpm-lock.yaml > yarn.lock > bun.lock(b) >
    package.json#packageManager > fallback to npm.
    """
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        return "bun"

    pkg_path = root / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            pm_field = pkg.get("packageManager", "")
            if pm_field.startswith("pnpm"):
                return "pnpm"
            if pm_field.startswith("yarn"):
                return "yarn"
            if pm_field.startswith("bun"):
                return "bun"
        except (json.JSONDecodeError, OSError):
            pass

    return "npm"


def _already_installed(root: Path, packages: List[str]) -> List[str]:
    """Return packages that are NOT already in package.json."""
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return packages
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        all_deps = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
        }
        return [p for p in packages if p not in all_deps]
    except (json.JSONDecodeError, OSError):
        return packages


def install_packages(root: Path, packages: List[str]) -> bool:
    """
    Install npm packages as dependencies.

    Skips packages already in package.json. Returns True on success,
    False on failure (prints a warning but does not raise).

    For npm, ``--legacy-peer-deps`` is added automatically to avoid
    ERESOLVE errors from strict peer dependency conflicts (e.g. the
    SDK may pin ``react@19.1.0`` while Next.js 16 ships ``react@19.2.x``).
    """
    to_install = _already_installed(root, packages)
    if not to_install:
        return True

    pm = detect_package_manager(root)
    cmd = [pm, "add"] + to_install
    # npm is strict about peer deps by default; --legacy-peer-deps avoids
    # ERESOLVE failures when transitive peer ranges don't overlap.
    if pm == "npm":
        cmd.append("--legacy-peer-deps")

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    try:
        subprocess.run(cmd, cwd=str(root), check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        console.print(
            f"[yellow]Warning: Failed to install dependencies.[/yellow]\n"
            f"  Please run manually: [bold]{' '.join(cmd)}[/bold]"
        )
        return False


def install_dev_packages(root: Path, packages: List[str]) -> bool:
    """
    Install npm packages as devDependencies.

    Same as install_packages but uses -D / --save-dev flag.
    """
    to_install = _already_installed(root, packages)
    if not to_install:
        return True

    pm = detect_package_manager(root)
    if pm == "yarn":
        cmd = [pm, "add", "--dev"] + to_install
    else:
        cmd = [pm, "add", "-D"] + to_install
    if pm == "npm":
        cmd.append("--legacy-peer-deps")

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    try:
        subprocess.run(cmd, cwd=str(root), check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(
            f"[yellow]Warning: Failed to install dev dependencies.[/yellow]\n"
            f"  Please run manually: [bold]{' '.join(cmd)}[/bold]"
        )
        return False
