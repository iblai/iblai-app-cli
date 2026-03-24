"""startapp command implementation."""

import os
from pathlib import Path
from typing import Optional

import click
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from iblai_cli.generators.agent import AgentAppGenerator

console = Console()


@click.command()
@click.argument("template", type=click.Choice(["agent"], case_sensitive=False))
@click.option(
    "--platform",
    "-p",
    help="Platform key (tenant identifier) for the app",
    type=str,
)
@click.option(
    "--agent",
    "-a",
    help="Agent ID / Mentor ID (required for agent template)",
    type=str,
)
@click.option(
    "--output",
    "-o",
    help="Output directory for the generated app",
    type=click.Path(),
    default=".",
)
@click.option(
    "--openai-key",
    help="OpenAI API key for AI-assisted generation",
    type=str,
    envvar="OPENAI_API_KEY",
)
@click.option(
    "--anthropic-key",
    help="Anthropic API key for AI-assisted generation",
    type=str,
    envvar="ANTHROPIC_API_KEY",
)
@click.option(
    "--ai-provider",
    help="AI provider to use (openai, anthropic)",
    type=click.Choice(["openai", "anthropic"], case_sensitive=False),
)
@click.option(
    "--prompt",
    "-P",
    help="Natural language prompt to customize the generated app (requires an AI key)",
    type=str,
)
@click.pass_context
def startapp(
    ctx: click.Context,
    template: str,
    platform: Optional[str],
    agent: Optional[str],
    output: str,
    openai_key: Optional[str],
    anthropic_key: Optional[str],
    ai_provider: Optional[str],
    prompt: Optional[str],
) -> None:
    """
    Create a new IBL.ai application from a template.

    TEMPLATE: The type of app to create (currently only 'agent' is supported)

    \b
    Examples:
        iblai startapp agent
        iblai startapp agent --platform acme
        iblai startapp agent --platform acme --agent my-agent-123
        iblai startapp agent --output ./my-app
        iblai startapp agent --platform acme --anthropic-key sk-...
        iblai startapp agent --prompt "Make this app for kids aged 5-10"
    """
    # If --prompt is provided, auto-enable AI
    if prompt and not (openai_key or anthropic_key):
        console.print(
            "[red]Error: --prompt requires an AI key. "
            "Set --anthropic-key / ANTHROPIC_API_KEY or --openai-key / OPENAI_API_KEY[/red]"
        )
        return

    # Determine AI configuration
    use_ai = bool(openai_key or anthropic_key)
    if use_ai:
        # Auto-detect provider if not specified
        if not ai_provider:
            if anthropic_key:
                ai_provider = "anthropic"
            elif openai_key:
                ai_provider = "openai"

    console.print(
        Panel.fit(
            f"[bold cyan]Creating new {template} app[/bold cyan]"
            + (
                " [bold yellow](AI-enhanced)[/bold yellow]"
                if prompt
                else " [bold yellow](AI-assisted)[/bold yellow]"
                if use_ai
                else ""
            ),
            border_style="cyan",
        )
    )

    if use_ai:
        console.print(
            f"[green]✓ AI assistance enabled[/green] (provider: {ai_provider})"
        )
    if prompt:
        console.print(f"[green]✓ Enhancement prompt:[/green] {prompt}")

    # Prompt for missing required parameters
    if not platform:
        questions = [
            inquirer.Text(
                "platform",
                message="Enter the platform key (tenant identifier)",
                validate=lambda _, x: len(x) > 0,
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[red]Operation cancelled[/red]")
            return
        platform = answers["platform"]

    # Require agent ID for the agent template
    if template.lower() == "agent" and not agent:
        questions = [
            inquirer.Text(
                "agent",
                message="Enter the agent ID (mentor ID)",
                validate=lambda _, x: len(x) > 0,
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[red]Operation cancelled[/red]")
            return
        agent = answers["agent"]

    # Prompt for app name
    default_name = f"{platform}-agent-app"
    questions = [
        inquirer.Text(
            "app_name",
            message="Enter the app name (will be used for directory and package.json)",
            default=default_name,
            validate=lambda _, x: (
                len(x) > 0 and x.replace("-", "").replace("_", "").isalnum()
            ),
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        console.print("[red]Operation cancelled[/red]")
        return
    app_name = answers["app_name"]

    # Determine output directory
    output_path = Path(output) / app_name
    if output_path.exists():
        console.print(f"[red]Error: Directory '{output_path}' already exists[/red]")
        return

    # Generate the app based on template
    try:
        if template.lower() == "agent":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating agent app...", total=None)

                generator = AgentAppGenerator(
                    app_name=app_name,
                    platform_key=platform,
                    mentor_id=agent,
                    output_dir=str(output_path),
                    use_ai=use_ai,
                    ai_provider=ai_provider,
                    openai_key=openai_key,
                    anthropic_key=anthropic_key,
                    prompt=prompt,
                )
                generator.generate()

                if prompt and generator.ai_helper:
                    progress.update(task, description="Enhancing with AI...")
                    generator.enhance_with_prompt()

                progress.update(task, completed=True)

            console.print()
            console.print(
                Panel.fit(
                    f"[bold green]✓ Successfully created {template} app![/bold green]"
                    + (" [bold yellow](AI-enhanced)[/bold yellow]" if prompt else "")
                    + "\n\n"
                    f"[cyan]App name:[/cyan] {app_name}\n"
                    f"[cyan]Platform:[/cyan] {platform}\n"
                    + (f"[cyan]Agent ID (Mentor ID):[/cyan] {agent}\n" if agent else "")
                    + (f"[cyan]AI Provider:[/cyan] {ai_provider}\n" if use_ai else "")
                    + (f"[cyan]Prompt:[/cyan] {prompt}\n" if prompt else "")
                    + f"[cyan]Location:[/cyan] {output_path}\n\n"
                    "[bold]Next steps:[/bold]\n"
                    f"  1. cd {output_path}\n"
                    "  2. pnpm install\n"
                    "  3. cp .env.example .env.local\n"
                    "  4. Update .env.local with your configuration\n"
                    "  5. pnpm dev\n\n"
                    "[bold]AI-assisted development:[/bold]\n"
                    "  A .mcp.json is included for Claude Code / Cursor integration.\n"
                    "  The MCP server provides component docs, hook info, and API patterns.",
                    border_style="green",
                    title="Success",
                )
            )

    except Exception as e:
        console.print(f"[red]Error generating app: {str(e)}[/red]")
        # Clean up partial directory if it was created
        if output_path.exists():
            import shutil

            shutil.rmtree(output_path)
        raise
