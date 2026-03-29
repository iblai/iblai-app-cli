"""``iblai config`` command — view and manage .env.local configuration."""

import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

# Known environment variables with their default values.
# These match the generated config.ts and .env.example templates.
KNOWN_VARS = {
    "NEXT_PUBLIC_API_BASE_URL": "https://api.iblai.app",
    "NEXT_PUBLIC_AUTH_URL": "https://login.iblai.app",
    "NEXT_PUBLIC_BASE_WS_URL": "wss://asgi.data.iblai.app",
    "NEXT_PUBLIC_PLATFORM_BASE_DOMAIN": "iblai.app",
    "NEXT_PUBLIC_MAIN_TENANT_KEY": "",
    "NEXT_PUBLIC_DEFAULT_AGENT_ID": "",
    "NEXT_PUBLIC_SUPPORT_EMAIL": "support@ibl.ai",
}

ENV_FILE = ".env.local"


def _read_env_local() -> dict[str, str]:
    """Read key=value pairs from .env.local (if it exists)."""
    env_path = Path(ENV_FILE)
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def _get_source(key: str, env_local: dict[str, str]) -> tuple[str, str]:
    """Return (value, source) for a known variable.

    Priority: .env.local > system env > default
    """
    if key in env_local:
        return env_local[key], ".env.local"
    sys_val = os.environ.get(key)
    if sys_val is not None:
        return sys_val, "system"
    default = KNOWN_VARS.get(key, "")
    if default:
        return default, "default"
    return "", "—"


@click.group()
def config():
    """View and manage .env.local configuration."""
    pass


@config.command("show")
def show():
    """Print the effective configuration for the current project.

    Shows all known environment variables with their current value
    and where the value comes from (.env.local, system env, or default).
    """
    env_local = _read_env_local()

    table = Table(
        title="ibl.ai Configuration",
        show_lines=True,
        border_style="blue",
    )
    table.add_column("Variable", style="cyan", min_width=35)
    table.add_column("Value", min_width=30)
    table.add_column("Source", style="dim", min_width=10)

    for key in KNOWN_VARS:
        value, source = _get_source(key, env_local)
        display_value = value if value else "[dim](not set)[/dim]"

        # Highlight source
        if source == ".env.local":
            source_style = "[green].env.local[/green]"
        elif source == "system":
            source_style = "[yellow]system[/yellow]"
        elif source == "default":
            source_style = "[dim]default[/dim]"
        else:
            source_style = "[dim]—[/dim]"

        table.add_row(key, display_value, source_style)

    console.print()
    console.print(table)
    console.print()

    env_path = Path(ENV_FILE)
    if not env_path.exists():
        console.print(
            "[yellow]No .env.local found.[/yellow] "
            "Copy .env.example to .env.local and configure your values:\n"
            "  cp .env.example .env.local"
        )


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_value(key, value):
    """Set a configuration value in .env.local.

    \b
    Examples:
      iblai config set NEXT_PUBLIC_MAIN_TENANT_KEY acme
      iblai config set NEXT_PUBLIC_AUTH_URL https://login.example.com
    """
    env_path = Path(ENV_FILE)
    lines = []
    found = False

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                line_key = stripped.partition("=")[0].strip()
                if line_key == key:
                    lines.append(f"{key}={value}")
                    found = True
                    continue
            lines.append(line)

    if not found:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green]Set[/green] {key}=[cyan]{value}[/cyan] in {ENV_FILE}")
