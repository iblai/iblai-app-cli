"""``iblai add`` command — add IBL.ai features to an existing project."""

from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from iblai_cli.project_detector import detect_project

console = Console()


def _require_nextjs():
    """Detect the project and abort if it isn't a Next.js App Router project."""
    project = detect_project(".")
    if project is None:
        console.print(
            "[red]Error: No package.json found in the current directory.[/red]"
        )
        console.print("Run this command from the root of your Next.js project.")
        raise SystemExit(1)
    if project.framework != "nextjs":
        console.print(
            "[red]Error: This project does not appear to be a Next.js app.[/red]"
        )
        console.print("Currently only Next.js (App Router) is supported.")
        raise SystemExit(1)
    if not project.has_app_router:
        console.print(
            "[yellow]Warning: No app/ directory detected. "
            "Files will be created assuming App Router layout.[/yellow]"
        )
    return project


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


@click.group()
def add():
    """Add IBL.ai features to an existing Next.js project.

    \b
    Available features:
      auth           SSO authentication (AuthProvider, TenantProvider, SSO callback)
      chat           AI chat widget (useAdvancedChat + WebSocket streaming)
      profile        User profile dropdown (avatar, settings, logout)
      notifications  Notification bell with unread badge
      mcp            MCP config + Claude skills for AI-assisted development
    """


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------


@add.command()
@click.option("--platform", "-p", help="Platform/tenant key", type=str, default=None)
def auth(platform: Optional[str]):
    """Add IBL.ai SSO authentication to your project."""
    project = _require_nextjs()

    if not platform:
        platform = click.prompt("Platform key (tenant identifier)")

    from iblai_cli.generators.add_auth import AddAuthGenerator

    gen = AddAuthGenerator(project, platform_key=platform)
    created = gen.generate()

    console.print()
    console.print(
        Panel.fit(
            "[bold green]Auth integration complete[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n"
            "  [cyan]Installed dependencies[/cyan]\n\n"
            "[bold]Next steps:[/bold]\n\n"
            "  1. Wrap your [bold]pages[/bold] (not root layout) with the provider:\n"
            '     [dim]import { IblaiProviders } from "@/providers/iblai-providers";[/dim]\n'
            "     [dim]<IblaiProviders>{children}</IblaiProviders>[/dim]\n\n"
            "     [yellow]Important:[/yellow] /sso-login-complete must NOT be inside\n"
            "     IblaiProviders. Use per-page wrapping or Next.js route groups.\n\n"
            "  2. Run [bold]pnpm dev[/bold] — unauthenticated users will be\n"
            "     redirected to the IBL Auth SPA automatically.",
            border_style="green",
            title="iblai add auth",
        )
    )


# ---------------------------------------------------------------------------
# chat
# ---------------------------------------------------------------------------


@add.command()
def chat():
    """Add an AI chat widget to your project."""
    project = _require_nextjs()

    # Check auth files exist
    if not (project.lib_dir / "iblai" / "config.ts").exists():
        console.print("[red]Error: Auth integration not found.[/red]")
        console.print("Run [bold]iblai add auth[/bold] first.")
        raise SystemExit(1)

    from iblai_cli.generators.add_chat import AddChatGenerator

    gen = AddChatGenerator(project)
    created = gen.generate()

    console.print()
    console.print(
        Panel.fit(
            "[bold green]Chat widget installed[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n"
            "  [cyan]Installed react-markdown + remark-gfm[/cyan]\n"
            "  [cyan]Added NEXT_PUBLIC_BASE_WS_URL to .env.local[/cyan]\n\n"
            "[bold]Usage:[/bold]\n\n"
            '  [dim]import { ChatWidget } from "@/components/iblai/chat-widget";[/dim]\n'
            '  [dim]<ChatWidget mentorId="your-mentor-id" />[/dim]',
            border_style="green",
            title="iblai add chat",
        )
    )


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


@add.command()
def profile():
    """Add a user profile dropdown to your project."""
    project = _require_nextjs()

    if not (project.lib_dir / "iblai" / "config.ts").exists():
        console.print("[red]Error: Auth integration not found.[/red]")
        console.print("Run [bold]iblai add auth[/bold] first.")
        raise SystemExit(1)

    from iblai_cli.generators.add_profile import AddProfileGenerator

    gen = AddProfileGenerator(project)
    created = gen.generate()

    console.print()
    console.print(
        Panel.fit(
            "[bold green]Profile dropdown installed[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n\n"
            "[bold]Usage:[/bold]\n\n"
            '  [dim]import { IblaiProfileDropdown } from "@/components/iblai/profile-dropdown";[/dim]\n'
            "  [dim]<IblaiProfileDropdown />[/dim]",
            border_style="green",
            title="iblai add profile",
        )
    )


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------


@add.command()
def notifications():
    """Add a notification bell to your project."""
    project = _require_nextjs()

    if not (project.lib_dir / "iblai" / "config.ts").exists():
        console.print("[red]Error: Auth integration not found.[/red]")
        console.print("Run [bold]iblai add auth[/bold] first.")
        raise SystemExit(1)

    from iblai_cli.generators.add_notifications import AddNotificationsGenerator

    gen = AddNotificationsGenerator(project)
    created = gen.generate()

    console.print()
    console.print(
        Panel.fit(
            "[bold green]Notification bell installed[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n\n"
            "[bold]Usage:[/bold]\n\n"
            '  [dim]import { IblaiNotificationBell } from "@/components/iblai/notification-bell";[/dim]\n'
            "  [dim]<IblaiNotificationBell />[/dim]",
            border_style="green",
            title="iblai add notifications",
        )
    )


# ---------------------------------------------------------------------------
# mcp
# ---------------------------------------------------------------------------


@add.command()
def mcp():
    """Add MCP server config and Claude skills for AI-assisted development."""
    project = _require_nextjs()

    from iblai_cli.generators.add_mcp import AddMcpGenerator

    gen = AddMcpGenerator(project)
    created = gen.generate()

    console.print()
    console.print(
        Panel.fit(
            "[bold green]MCP + Claude skills installed[/bold green]\n\n"
            "[bold]Applied:[/bold]\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n"
            "  [cyan]Installed @iblai/mcp (devDependency)[/cyan]\n\n"
            "[bold]What you get:[/bold]\n\n"
            "  - .mcp.json: Claude Code / Cursor will auto-detect the @iblai/mcp server\n"
            "  - .claude/skills/: Slash commands for guided IBL.ai integration\n\n"
            "[bold]Available Claude skills:[/bold]\n\n"
            "  /iblai-add-auth           Add SSO auth step-by-step\n"
            "  /iblai-add-chat           Add AI chat widget step-by-step\n"
            "  /iblai-add-profile        Add profile dropdown step-by-step\n"
            "  /iblai-add-notifications  Add notification bell step-by-step\n"
            "  /iblai-setup              Full setup from scratch",
            border_style="green",
            title="iblai add mcp",
        )
    )
