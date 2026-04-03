"""startapp command implementation."""

import os
from pathlib import Path
from typing import Optional

import click
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from iblai.config import load_config
from iblai.generators.agent import AgentAppGenerator

console = Console()


@click.command()
@click.argument("template", type=click.Choice(["agent"], case_sensitive=False))
@click.option(
    "--platform",
    "-p",
    help="Platform key (tenant identifier) for the app",
    type=str,
    envvar=["IBLAI_PLATFORM_KEY", "PLATFORM"],
)
@click.option(
    "--agent",
    "-a",
    help="Agent ID (optional)",
    type=str,
    envvar="IBLAI_AGENT_ID",
)
@click.option(
    "--app-name",
    help="App name (used for directory and package.json)",
    type=str,
    envvar="IBLAI_APP_NAME",
)
@click.option(
    "--output",
    "-o",
    help="Output directory for the generated app",
    type=click.Path(),
    default=".",
    envvar="IBLAI_OUTPUT_DIR",
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
    envvar="IBLAI_AI_PROVIDER",
)
@click.option(
    "--ai-model",
    help="AI model to use (e.g., claude-sonnet-4-20250514, gpt-4-turbo-preview)",
    type=str,
    envvar="IBLAI_AI_MODEL",
)
@click.option(
    "--ai-temperature",
    help="AI temperature for generation (0.0-2.0)",
    type=float,
    envvar="IBLAI_AI_TEMPERATURE",
)
@click.option(
    "--ai-max-tokens",
    help="AI max tokens for generation",
    type=int,
    envvar="IBLAI_AI_MAX_TOKENS",
)
@click.option(
    "--prompt",
    "-P",
    help="Natural language prompt to customize the generated app (requires an AI key)",
    type=str,
    envvar="IBLAI_PROMPT",
)
@click.option(
    "--env-file",
    help="Path to a custom .env file (default: .env in current directory)",
    type=click.Path(exists=True),
)
@click.option(
    "--stage",
    help="Stage name to load .env.{stage} overrides (e.g., production, staging)",
    type=str,
    envvar="DEV_STAGE",
)
@click.option(
    "--builds",
    is_flag=True,
    default=False,
    help="Include desktop/mobile build support (Tauri v2, generates src-tauri/)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip all interactive prompts (requires --platform and --app-name)",
)
@click.pass_context
def startapp(
    ctx: click.Context,
    template: str,
    platform: Optional[str],
    agent: Optional[str],
    app_name: Optional[str],
    output: str,
    openai_key: Optional[str],
    anthropic_key: Optional[str],
    ai_provider: Optional[str],
    ai_model: Optional[str],
    ai_temperature: Optional[float],
    ai_max_tokens: Optional[int],
    prompt: Optional[str],
    env_file: Optional[str],
    stage: Optional[str],
    builds: bool = False,
    yes: bool = False,
) -> None:
    """
    Create a new ibl.ai application from a template.

    TEMPLATE: The type of app to create (currently only 'agent' is supported)

    \b
    Configuration priority (highest wins):
        CLI flags > System env vars > .env.{DEV_STAGE} > .env > interactive prompts

    \b
    Examples:
        iblai startapp agent
        iblai startapp agent --platform acme
        iblai startapp agent --platform acme --agent my-agent-123
        iblai startapp agent --output ./my-app
        iblai startapp agent --platform acme --anthropic-key sk-...
        iblai startapp agent --prompt "Make this app for kids aged 5-10"
        iblai startapp agent --env-file ./config/.env --stage production
        iblai startapp agent --ai-model claude-sonnet-4-20250514 --ai-temperature 0.5
    """
    # If --env-file or --stage was explicitly provided, re-load config
    # to pick up the custom file or stage overrides.
    # (The default .env was already loaded in cli.py at import time.)
    if env_file or stage:
        load_config(env_file=env_file, stage=stage)
        # Re-read values that Click already resolved as None from env
        # (Click resolved them before the re-load, so we fill them in)
        if not platform:
            platform = os.environ.get("IBLAI_PLATFORM_KEY")
        if not agent:
            agent = os.environ.get("IBLAI_AGENT_ID")
        if not app_name:
            app_name = os.environ.get("IBLAI_APP_NAME")
        if not openai_key:
            openai_key = os.environ.get("OPENAI_API_KEY")
        if not anthropic_key:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not ai_provider:
            ai_provider = os.environ.get("IBLAI_AI_PROVIDER")
        if not ai_model:
            ai_model = os.environ.get("IBLAI_AI_MODEL")
        if ai_temperature is None:
            raw = os.environ.get("IBLAI_AI_TEMPERATURE")
            if raw:
                ai_temperature = float(raw)
        if ai_max_tokens is None:
            raw = os.environ.get("IBLAI_AI_MAX_TOKENS")
            if raw:
                ai_max_tokens = int(raw)
        if not prompt:
            prompt = os.environ.get("IBLAI_PROMPT")

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
        if ai_model:
            console.print(f"[green]✓ Model:[/green] {ai_model}")
        if ai_temperature is not None:
            console.print(f"[green]✓ Temperature:[/green] {ai_temperature}")
        if ai_max_tokens is not None:
            console.print(f"[green]✓ Max tokens:[/green] {ai_max_tokens}")
    if prompt:
        console.print(f"[green]✓ Enhancement prompt:[/green] {prompt}")

    # Non-interactive mode: validate required values
    if yes:
        if not platform:
            console.print("[red]Error: --platform is required when using --yes[/red]")
            raise SystemExit(1)
        if not app_name:
            console.print("[red]Error: --app-name is required when using --yes[/red]")
            raise SystemExit(1)

    # Prompt for missing required parameters (skipped with --yes)
    if not platform and not yes:
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

    # Require agent ID for the agent template (skipped with --yes)
    if template.lower() == "agent" and not agent and not yes:
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

    # Prompt for app name if not provided via flag or env (skipped with --yes)
    interactive = not app_name and not yes
    if interactive:
        questions = [
            inquirer.Text(
                "app_name",
                message="Enter the app name (will be used for directory and package.json)",
                default=f"{platform}-agent-app",
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

    # Ask about Tauri integration (interactive mode only, when --builds was not passed)
    if interactive and not builds:
        questions = [
            inquirer.Confirm(
                "builds",
                message=(
                    "Include desktop/mobile build support?"
                    " (Tauri v2 — generates src-tauri/, enables native builds)"
                ),
                default=False,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers:
            builds = answers["builds"]

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
                    ai_model=ai_model,
                    ai_temperature=ai_temperature,
                    ai_max_tokens=ai_max_tokens,
                    builds=builds,
                )
                generator.generate()

                if prompt and generator.ai_helper:
                    progress.update(task, description="Enhancing with AI...")
                    generator.enhance_with_prompt()

                if builds:
                    progress.update(task, description="Adding Tauri desktop shell...")
                    from iblai.generators.add_builds import AddBuildsGenerator

                    tauri_gen = AddBuildsGenerator(
                        project_root=str(output_path),
                        app_name=app_name,
                    )
                    tauri_gen.generate()

                progress.update(task, completed=True)

            console.print()
            console.print(
                Panel.fit(
                    f"[bold green]✓ Successfully created {template} app![/bold green]"
                    + (" [bold yellow](AI-enhanced)[/bold yellow]" if prompt else "")
                    + "\n\n"
                    f"[cyan]App name:[/cyan] {app_name}\n"
                    f"[cyan]Platform:[/cyan] {platform}\n"
                    + (f"[cyan]Agent ID:[/cyan] {agent}\n" if agent else "")
                    + (f"[cyan]AI Provider:[/cyan] {ai_provider}\n" if use_ai else "")
                    + (f"[cyan]AI Model:[/cyan] {ai_model}\n" if ai_model else "")
                    + (f"[cyan]Prompt:[/cyan] {prompt}\n" if prompt else "")
                    + (f"[cyan]Tauri:[/cyan] enabled\n" if builds else "")
                    + f"[cyan]Location:[/cyan] {output_path}\n\n"
                    "[bold]Next steps:[/bold]\n"
                    f"  1. cd {output_path}\n"
                    "  2. pnpm install\n"
                    "  3. cp .env.example .env.local\n"
                    "  4. Update .env.local with your configuration\n"
                    + (
                        "  5. iblai builds dev  (desktop + web dev server)\n\n"
                        if builds
                        else "  5. pnpm dev\n\n"
                    )
                    + (
                        "[bold]Tauri desktop app:[/bold]\n"
                        "  iblai builds dev              Start desktop dev mode\n"
                        "  iblai builds build            Build for distribution\n"
                        "  iblai builds iconography logo.png     Generate app icons\n"
                        "  iblai builds ci-workflow      Generate CI build workflows\n\n"
                        "[bold]iOS (macOS with Xcode required):[/bold]\n"
                        "  iblai builds ios init         Initialize iOS project (run once)\n"
                        "  pnpm tauri:dev:ios           Run in iOS Simulator\n"
                        "  pnpm tauri:build:ios         Build iOS app (.ipa)\n\n"
                        "[bold]Android:[/bold]\n"
                        "  iblai builds android init     Initialize Android project\n"
                        "  iblai builds android dev      Run on emulator/device\n\n"
                        if builds
                        else ""
                    )
                    + "[bold]AI-assisted development:[/bold]\n"
                    "  A .mcp.json is included for Claude Code / Cursor integration.\n"
                    "  The MCP server provides component docs, hook info, and API patterns.\n\n"
                    "[bold]Add UI blocks (shadcnspace):[/bold]\n"
                    "  npx shadcn@latest add @shadcn-space/hero-01\n"
                    "  npx shadcn@latest add @shadcn-space/dashboard-shell-01\n"
                    "  Browse all: https://shadcnspace.com/blocks",
                    border_style="green",
                    title="Success",
                )
            )
        else:
            console.print(f"[red]Error: Unknown template '{template}'[/red]")
            return

    except Exception as e:
        console.print(f"[red]Error generating app: {str(e)}[/red]")
        # Clean up partial directory if it was created
        if output_path.exists():
            import shutil

            shutil.rmtree(output_path)
        raise
