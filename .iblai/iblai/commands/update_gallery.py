"""``iblai update-gallery`` command -- regenerate the Component Gallery."""

from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.command("update-gallery")
@click.argument(
    "path",
    type=click.Path(exists=True),
)
@click.option(
    "--screenshots",
    is_flag=True,
    default=False,
    help="Generate component screenshots via Playwright.",
)
@click.option(
    "--platform",
    envvar="IBLAI_PLATFORM_KEY",
    default=None,
    help="Platform key (required with --screenshots).",
)
@click.option(
    "--username",
    envvar="PLAYWRIGHT_USERNAME",
    default=None,
    help="Login email for authentication (required with --screenshots).",
)
@click.option(
    "--password",
    envvar="PLAYWRIGHT_PASSWORD",
    default=None,
    help="Login password for authentication (required with --screenshots).",
)
def update_gallery(
    path: str,
    screenshots: bool,
    platform: str,
    username: str,
    password: str,
):
    """Regenerate the Component Gallery section in a SKILL.md file.

    PATH can be a skills directory (containing iblai-components/SKILL.md)
    or a direct path to a SKILL.md file.

    Fetches the latest @iblai/web-containers npm package, extracts
    .d.ts type declarations, discovers all exported React components, and
    rewrites the Component Gallery section.

    With --screenshots, also scaffolds a temp Next.js app, renders each
    component category, and saves PNG screenshots next to the SKILL.md.

    \b
    Usage:
      iblai update-gallery skills/
      iblai update-gallery skills/iblai-components/SKILL.md
      iblai update-gallery skills/ --screenshots --platform acme \\
        --username admin@acme.com --password s3cret
    """
    from iblai.gallery import (
        generate_screenshots as _gen_screenshots,
        resolve_skill_path,
        update_gallery as _update,
    )

    # Resolve the actual SKILL.md path early for screenshots
    try:
        skill_path = resolve_skill_path(path)
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    screenshot_map = None

    if screenshots:
        missing = []
        if not platform:
            missing.append("--platform / IBLAI_PLATFORM_KEY")
        if not username:
            missing.append("--username / PLAYWRIGHT_USERNAME")
        if not password:
            missing.append("--password / PLAYWRIGHT_PASSWORD")
        if missing:
            console.print(
                f"[red]Error: --screenshots requires: {', '.join(missing)}[/red]"
            )
            raise SystemExit(1)

        skill_dir = skill_path.parent
        console.print("[cyan]Generating component screenshots...[/cyan]")
        try:
            screenshot_map = _gen_screenshots(
                skill_dir, platform, username, password
            )
            console.print(
                f"[green]Captured {len(screenshot_map)} screenshots[/green]"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Screenshot generation failed: {e}[/yellow]")
            console.print("[dim]Continuing with gallery update without screenshots...[/dim]")

    console.print(
        "[cyan]Fetching @iblai/web-containers from npm registry...[/cyan]"
    )

    try:
        version, updated_content, export_count, resolved_path = _update(
            path, screenshot_map
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)

    Path(resolved_path).write_text(updated_content, encoding="utf-8")

    console.print(
        f"[green]Updated Component Gallery[/green] "
        f"({export_count} exports from @iblai/web-containers@{version})"
    )
    console.print(f"  [dim]{resolved_path}[/dim]")
