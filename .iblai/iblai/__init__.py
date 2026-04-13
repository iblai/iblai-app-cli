"""ibl.ai CLI - Command-line tool to scaffold ibl.ai applications."""

__version__ = "1.2.1"
__author__ = "ibl.ai"
__email__ = "support@ibl.ai"
__repo__ = "https://github.com/iblai/iblai-app-cli"
__commit__ = ""  # Set by build script for binary builds


def get_commit() -> str:
    """Return the short git commit ID.

    Tries the baked value first (set by PyInstaller build script),
    then falls back to running ``git rev-parse --short HEAD``.
    """
    if __commit__:
        return __commit__
    try:
        import subprocess
        from pathlib import Path

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent.parent.parent,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"
