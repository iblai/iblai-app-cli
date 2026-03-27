"""Main CLI entry point for iblai command."""

import click
from rich.console import Console

from iblai import __version__
from iblai.config import load_config
from iblai.commands.startapp import startapp
from iblai.commands.add import add
from iblai.commands.builds import builds

# Load .env and .env.{DEV_STAGE} before Click parses options.
# This injects values into os.environ so Click's envvar= resolves them.
load_config()

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="iblai")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    IBL.ai CLI - Quickly scaffold IBL.ai applications.

    Use 'iblai COMMAND --help' for more information on a specific command.
    """
    ctx.ensure_object(dict)
    ctx.obj["console"] = console


# Register commands
cli.add_command(startapp)
cli.add_command(add)
cli.add_command(builds)


if __name__ == "__main__":
    cli()
