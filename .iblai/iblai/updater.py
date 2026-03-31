"""Auto-update logic for the iblai CLI.

Checks for newer versions and self-updates using the same mechanism
that originally installed the CLI (pip, npm, or binary replacement).

The check is cached for 24 hours in ~/.iblai/update-check.json to
avoid hitting the network on every invocation.  Updates can be disabled
with ``--no-update`` or ``IBLAI_NO_UPDATE=1``.
"""

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import click
import requests

from iblai import __version__

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DIR = Path.home() / ".iblai"
CACHE_FILE = CACHE_DIR / "update-check.json"
CACHE_TTL = 86400  # 24 hours in seconds

PYPI_URL = "https://pypi.org/pypi/iblai-app-cli/json"
GITHUB_API_URL = "https://api.github.com/repos/iblai/iblai-app-cli/releases/latest"
REQUEST_TIMEOUT = 5  # seconds — fast fail on bad networks

# GitHub release asset names, keyed by (system, machine).
BINARY_ASSETS = {
    ("Linux", "x86_64"): "iblai-linux-x64",
    ("Linux", "aarch64"): "iblai-linux-arm64",
    ("Darwin", "arm64"): "iblai-darwin-arm64",
    ("Windows", "AMD64"): "iblai-win32-x64.exe",
    ("Windows", "ARM64"): "iblai-win32-arm64.exe",
}


# ---------------------------------------------------------------------------
# Install method detection
# ---------------------------------------------------------------------------


def detect_install_method() -> str:
    """Detect how the CLI was installed.

    Returns one of: ``"binary"``, ``"npm"``, ``"npx"``, ``"dev"``, ``"pip"``.
    """
    # 1. PyInstaller frozen binary
    if getattr(sys, "_MEIPASS", None):
        return "binary"

    file_path = os.path.abspath(__file__)
    exe_path = os.path.abspath(sys.executable)

    # 2. npx — temp cache directory (each invocation fetches latest, skip)
    for p in (file_path, exe_path):
        normalized = p.replace("\\", "/")
        if "_npx/" in normalized:
            return "npx"

    # 3. npm — binary lives inside a node_modules tree
    for p in (file_path, exe_path):
        normalized = p.replace("\\", "/")
        if "node_modules/@iblai/" in normalized or "node_modules\\@iblai\\" in p:
            return "npm"

    # 4. Dev install (pip install -e .)
    source_dir = Path(file_path).resolve().parent.parent
    if (source_dir / "pyproject.toml").exists() and (source_dir / ".git").exists():
        return "dev"

    # 5. pip (standard site-packages install)
    return "pip"


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------


def _parse_version(version_str: str) -> tuple:
    """Parse ``"0.2.0"`` or ``"v0.2.0"`` into a comparable tuple."""
    v = version_str.lstrip("v")
    parts = []
    for part in v.split("."):
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(remote: str, local: str) -> bool:
    """Return True if *remote* is strictly newer than *local*."""
    return _parse_version(remote) > _parse_version(local)


# ---------------------------------------------------------------------------
# Version fetching
# ---------------------------------------------------------------------------


def get_latest_version(install_method: str) -> Optional[str]:
    """Fetch the latest published version from the appropriate registry.

    Returns the version string or ``None`` on failure.
    """
    try:
        if install_method in ("pip", "dev"):
            resp = requests.get(PYPI_URL, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()["info"]["version"]
        else:
            resp = requests.get(
                GITHUB_API_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/vnd.github+json"},
            )
            resp.raise_for_status()
            tag = resp.json()["tag_name"]
            return tag.lstrip("v")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _read_cache() -> Optional[dict]:
    """Read the update-check cache file."""
    try:
        if CACHE_FILE.exists():
            data = json.loads(CACHE_FILE.read_text())
            if isinstance(data, dict) and "checked_at" in data:
                return data
    except Exception:
        pass
    return None


def _write_cache(latest_version: Optional[str]) -> None:
    """Write the update-check result to cache."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "checked_at": time.time(),
            "current_version": __version__,
            "latest_version": latest_version,
        }
        CACHE_FILE.write_text(json.dumps(payload, indent=2) + "\n")
    except Exception:
        pass


def check_for_update(install_method: str) -> Optional[str]:
    """Check if a newer version is available, respecting the 24 h cache.

    Returns the new version string if an update is available, else ``None``.
    """
    cache = _read_cache()
    if cache is not None:
        age = time.time() - cache.get("checked_at", 0)
        if age < CACHE_TTL and cache.get("current_version") == __version__:
            cached_latest = cache.get("latest_version")
            if cached_latest and _is_newer(cached_latest, __version__):
                return cached_latest
            return None

    latest = get_latest_version(install_method)
    _write_cache(latest)

    if latest and _is_newer(latest, __version__):
        return latest
    return None


# ---------------------------------------------------------------------------
# Privilege escalation helpers
# ---------------------------------------------------------------------------


def _find_sudo() -> Optional[str]:
    """Find ``sudo`` or ``doas`` on the system."""
    for cmd in ("sudo", "doas"):
        if shutil.which(cmd):
            return cmd
    return None


def _ask_sudo(sudo_cmd: str, action: str) -> bool:
    """Prompt the user before escalating privileges.

    Returns ``True`` if the user agrees.
    """
    return click.confirm(
        f"Update requires elevated privileges ({action}). Use {sudo_cmd}?",
        default=True,
        err=True,
    )


# ---------------------------------------------------------------------------
# Update execution
# ---------------------------------------------------------------------------


def _update_pip(new_version: str) -> bool:
    """Update via ``pip install --upgrade``."""
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "iblai-app-cli",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        return True

    # Permission error — try with sudo/doas
    if "Permission" in (result.stderr or ""):
        sudo = _find_sudo()
        if sudo and _ask_sudo(sudo, "pip install"):
            result = subprocess.run(
                [sudo] + cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
    return False


def _update_npm() -> bool:
    """Update via ``npm install -g @iblai/cli@latest``."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm_cmd, "install", "-g", "@iblai/cli@latest"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        return True

    if "permission" in (result.stderr or "").lower():
        sudo = _find_sudo()
        if sudo and _ask_sudo(sudo, "npm install"):
            result = subprocess.run(
                [sudo] + cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
    return False


def _get_binary_asset_name() -> Optional[str]:
    """Return the GitHub release asset name for the current platform."""
    system = platform.system()
    machine = platform.machine()
    return BINARY_ASSETS.get((system, machine))


def _update_binary(new_version: str) -> bool:
    """Download the new binary from GitHub Releases and replace the current one."""
    asset_name = _get_binary_asset_name()
    if not asset_name:
        return False

    current_binary = Path(sys.executable).resolve()
    binary_dir = current_binary.parent
    download_url = (
        f"https://github.com/iblai/iblai-app-cli/releases/download/"
        f"v{new_version}/{asset_name}"
    )

    try:
        fd, tmp_path_str = tempfile.mkstemp(
            dir=str(binary_dir),
            prefix=".iblai-update-",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_path_str)
        try:
            resp = requests.get(download_url, stream=True, timeout=30)
            resp.raise_for_status()
            with os.fdopen(fd, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        # Set executable permission
        if sys.platform != "win32":
            tmp_path.chmod(
                tmp_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )

        # Try atomic replacement
        backup_path = current_binary.with_suffix(current_binary.suffix + ".bak")
        try:
            if backup_path.exists():
                backup_path.unlink()
            current_binary.rename(backup_path)
            tmp_path.rename(current_binary)
        except PermissionError:
            if sys.platform == "win32":
                # Windows: running exe is locked
                pending = current_binary.with_suffix(".pending")
                tmp_path.rename(pending)
                click.echo(
                    f"Update downloaded to {pending}. "
                    f"Please replace {current_binary.name} manually.",
                    err=True,
                )
                return False
            # Unix: try with sudo
            sudo = _find_sudo()
            if sudo and _ask_sudo(sudo, "replace binary"):
                subprocess.run(
                    [sudo, "mv", str(tmp_path), str(current_binary)],
                    check=True,
                )
            else:
                tmp_path.unlink(missing_ok=True)
                return False

        # Clean up backup
        try:
            backup_path.unlink(missing_ok=True)
        except Exception:
            pass

        return True

    except Exception:
        return False


def perform_update(install_method: str, new_version: str) -> bool:
    """Execute the update for the detected install method."""
    try:
        if install_method == "pip":
            return _update_pip(new_version)
        elif install_method == "npm":
            return _update_npm()
        elif install_method == "binary":
            return _update_binary(new_version)
        else:
            return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def auto_update() -> None:
    """Check for updates and apply them if available.

    Called from ``cli.py`` before Click dispatches to a subcommand.
    Completely non-destructive: any failure at any stage results in a
    silent fall-through so the user's command still runs.
    """
    try:
        install_method = detect_install_method()

        # Never auto-update editable/dev installs or npx invocations
        if install_method in ("dev", "npx"):
            return

        new_version = check_for_update(install_method)
        if not new_version:
            return

        click.echo(
            f"Updating iblai {__version__} \u2192 {new_version} ({install_method})...",
            err=True,
        )

        success = perform_update(install_method, new_version)

        if success:
            click.echo(
                f"Updated to {new_version}. Restart to use the new version.",
                err=True,
            )
            _write_cache(new_version)
        else:
            click.echo(
                "Update failed \u2014 continuing with current version.",
                err=True,
            )

    except Exception:
        # Never let the updater crash the CLI
        pass
