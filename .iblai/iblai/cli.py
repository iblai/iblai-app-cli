"""Main CLI entry point for iblai command."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from iblai import __version__
from iblai.config import load_config
from iblai.commands.startapp import startapp
from iblai.commands.add import add
from iblai.commands.builds import builds

# Load .env and .env.{DEV_STAGE} before Click parses options.
# This injects values into os.environ so Click's envvar= resolves them.
load_config()

console = Console()


def _show_welcome():
    """Print a rich welcome screen when iblai is run with no arguments."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan", min_width=30)
    table.add_column()

    table.add_row("", "")
    table.add_row("[bold]Create[/bold]", "")
    table.add_row("  iblai startapp agent", "Full app with AI chat + SSO auth")
    table.add_row("  iblai startapp base", "Minimal app with auth only")
    table.add_row("", "")
    table.add_row("[bold]Add to existing app[/bold]", "")
    table.add_row("  iblai add auth", "SSO authentication")
    table.add_row("  iblai add chat", "AI chat widget")
    table.add_row("  iblai add profile", "User profile page")
    table.add_row("  iblai add account", "Account settings")
    table.add_row("  iblai add analytics", "Analytics dashboard")
    table.add_row("  iblai add notifications", "Notification bell")
    table.add_row("  iblai add mcp", "MCP server + AI skills")
    table.add_row("  iblai add builds", "Desktop/mobile (Tauri v2)")
    table.add_row("", "")
    table.add_row("[bold]Desktop/mobile builds[/bold]", "")
    table.add_row("  iblai builds dev", "Dev mode (Next.js + native shell)")
    table.add_row("  iblai builds build", "Production build")
    table.add_row("  iblai builds generate-icons", "Generate app icons")
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
@click.version_option(version=__version__, prog_name="iblai")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    ibl.ai CLI - Quickly scaffold ibl.ai applications.

    Use 'iblai COMMAND --help' for more information on a specific command.
    """
    ctx.ensure_object(dict)
    ctx.obj["console"] = console
    if ctx.invoked_subcommand is None:
        _show_welcome()


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


# Register commands
cli.add_command(startapp)
cli.add_command(add)
cli.add_command(builds)


if __name__ == "__main__":
    cli()
