"""Main CLI entry point for iblai command."""

import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from iblai import __version__, __repo__, get_commit
from iblai.config import load_config
from iblai.commands.startapp import startapp
from iblai.commands.add import add
from iblai.commands.builds import builds
from iblai.commands.config import config
from iblai.commands.deploy import deploy
from iblai.commands.update_gallery import update_gallery

# Load .env and .env.{DEV_STAGE} before Click parses options.
# This injects values into os.environ so Click's envvar= resolves them.
load_config()

console = Console()


def _version_callback(ctx, param, value):
    """Custom --version callback that shows repo URL and commit."""
    if not value:
        return
    commit = get_commit()
    console.print(f"iblai, version {__version__}")
    console.print(f"Repo: {__repo__}")
    console.print(f"Commit: {commit}")
    ctx.exit()


def _show_welcome():
    """Print a rich welcome screen when iblai is run with no arguments."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", min_width=30)
    table.add_column()

    table.add_row("", "")
    table.add_row("[bold]Create[/bold]", "")
    table.add_row("  iblai startapp agent", "Full app with AI chat + SSO auth")
    table.add_row("", "")
    table.add_row("[bold]Add to existing app[/bold]", "")
    table.add_row("  iblai add auth", "SSO authentication")
    table.add_row("  iblai add chat", "AI chat widget")
    table.add_row("  iblai add profile", "User profile page")
    table.add_row("  iblai add account", "Account settings")
    table.add_row("  iblai add analytics", "Analytics dashboard")
    table.add_row("  iblai add notification", "Notification bell")
    table.add_row("  iblai add mcp", "MCP server + AI skills")
    table.add_row("  iblai add builds", "Desktop/mobile (Tauri v2)")
    table.add_row("", "")
    table.add_row("[bold]Desktop/mobile builds[/bold]", "")
    table.add_row("  iblai builds dev", "Dev mode (Next.js + native shell)")
    table.add_row("  iblai builds build", "Production build")
    table.add_row("  iblai builds iconography", "Generate app icons")
    table.add_row("  iblai builds device", "List simulators/emulators")
    table.add_row("  iblai builds screenshot", "Generate screenshot script")
    table.add_row("", "")
    table.add_row("[bold]Deploy[/bold]", "")
    table.add_row("  iblai deploy vercel", "Deploy frontend to Vercel")
    table.add_row("", "")
    table.add_row("[bold]Quick actions[/bold]", "")
    table.add_row("  iblai init", "Configure AI-assisted development")
    table.add_row("  iblai open", "Open local dev server in browser")
    table.add_row("  iblai info", "Show version, repo, and commit")
    table.add_row("  iblai config show", "View current configuration")
    table.add_row("  iblai config set KEY VAL", "Update .env.local")
    table.add_row("  iblai update-gallery skills/", "Regenerate component gallery")
    table.add_row("", "")
    table.add_row("[bold]Repo[/bold]", __repo__)
    table.add_row("  examples/iblai-agent-app/", "Reference implementation")
    table.add_row("  skills/", "AI assistant skills")
    table.add_row("  BRAND.md", "Brand identity guide")
    table.add_row("", "")

    console.print()
    console.print(
        Panel(
            table,
            title=f"[bold]ibl.ai App CLI[/bold] v{__version__}",
            subtitle="[dim]iblai COMMAND --help for details[/dim]",
            border_style="blue",
        )
    )
    console.print()


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    callback=_version_callback,
    expose_value=False,
    is_eager=True,
    help="Show version, repo, and commit.",
)
@click.option(
    "--no-update",
    is_flag=True,
    default=False,
    help="Skip automatic update check.",
)
@click.pass_context
def cli(ctx: click.Context, no_update: bool) -> None:
    """
    ibl.ai CLI - Quickly scaffold ibl.ai applications.

    Use 'iblai COMMAND --help' for more information on a specific command.
    """
    ctx.ensure_object(dict)
    ctx.obj["console"] = console

    # Auto-update check (before any subcommand runs)
    if not no_update and not os.environ.get("IBLAI_NO_UPDATE"):
        from iblai.updater import auto_update

        auto_update()

    if ctx.invoked_subcommand is None:
        _show_welcome()


# ---------------------------------------------------------------------------
# iblai info — show version, repo, commit, environment details
# ---------------------------------------------------------------------------


@cli.command("info")
def info_cmd():
    """Show CLI version, repo, commit, and environment details."""
    import platform
    import sys

    commit = get_commit()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", min_width=20)
    table.add_column()

    table.add_row("Version", __version__)
    table.add_row("Commit", commit)
    table.add_row("Repo", __repo__)
    table.add_row(
        "Python",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row("Platform", f"{platform.system()} {platform.machine()}")
    table.add_row("Executable", sys.executable)

    console.print()
    console.print(Panel(table, title="[bold]ibl.ai CLI[/bold]", border_style="blue"))
    console.print()


# ---------------------------------------------------------------------------
# iblai init — alias for iblai add mcp (agent-native onboarding)
# ---------------------------------------------------------------------------


@cli.command("init")
def init_cmd():
    """Configure the current project for AI-assisted development with ibl.ai.

    \b
    Adds .mcp.json, skills/, and tool symlinks for Claude Code, OpenCode,
    and Cursor. This is equivalent to 'iblai add mcp'.
    """
    from pathlib import Path

    from iblai.generators.add_mcp import AddMcpGenerator
    from iblai.project_detector import detect_project

    project = detect_project(".")
    if project is None:
        console.print(
            "[red]Error: No package.json found in the current directory.[/red]"
        )
        console.print("Run this command from the root of your Next.js project.")
        raise SystemExit(1)

    gen = AddMcpGenerator(project)
    created = gen.generate()

    console.print()
    console.print(
        Panel(
            "[bold green]Project initialized for AI-assisted development[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created[:5])
            + (
                f"\n  [dim]... and {len(created) - 5} more files[/dim]"
                if len(created) > 5
                else ""
            )
            + "\n\n"
            "[bold]What was added:[/bold]\n"
            "  .mcp.json           MCP server configuration\n"
            "  skills/             AI assistant skills (Claude, OpenCode, Cursor)\n"
            "  .claude/skills/     Symlinks for Claude Code\n"
            "  .opencode/skills/   Symlinks for OpenCode\n"
            "  .cursor/rules/      Symlinks for Cursor\n\n"
            "[bold]Next steps:[/bold]\n"
            "  Open this project in Claude Code, OpenCode, or Cursor.\n"
            "  Type [cyan]/[/cyan] to see available skills.",
            border_style="green",
            title="iblai init",
        )
    )


# ---------------------------------------------------------------------------
# iblai open — open local dev server or docs in browser
# ---------------------------------------------------------------------------


@cli.command("open")
@click.argument("target", default="app", required=False)
def open_cmd(target):
    """Open the local dev server or docs in your browser.

    \b
    Targets:
      app   (default) Open http://localhost:3000
      docs  Open the documentation on GitHub
    """
    import webbrowser

    urls = {
        "app": "http://localhost:3000",
        "docs": __repo__,
    }
    url = urls.get(target)
    if not url:
        console.print(f"[red]Unknown target: {target}[/red]")
        console.print("Available targets: app, docs")
        raise SystemExit(1)
    console.print(f"[cyan]Opening {url}...[/cyan]")
    webbrowser.open(url)


# Register commands
cli.add_command(startapp)
cli.add_command(add)
cli.add_command(builds)
cli.add_command(config)
cli.add_command(deploy)
cli.add_command(update_gallery)


if __name__ == "__main__":
    cli()
