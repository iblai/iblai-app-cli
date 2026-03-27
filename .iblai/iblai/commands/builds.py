"""iblai builds -- Tauri v2 build and development commands.

Thin wrapper around @tauri-apps/cli (installed via npm/pnpm/bun).
All arguments except ``init`` and ``ci-workflow`` are passed directly
through to the ``tauri`` binary resolved from node_modules.

Requires the Rust toolchain (rustc + cargo) for compilation.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_rust() -> bool:
    """Return True if rustc and cargo are in PATH."""
    return shutil.which("rustc") is not None and shutil.which("cargo") is not None


def _require_rust():
    """Exit with a helpful message when the Rust toolchain is missing."""
    if _has_rust():
        return
    console.print(
        Panel(
            "[bold red]Rust toolchain not found[/bold red]\n\n"
            "Tauri requires the Rust toolchain (rustc + cargo).\n\n"
            "[bold]Install Rust:[/bold]\n"
            "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh\n\n"
            "Or visit: [cyan]https://rustup.rs[/cyan]\n\n"
            "After installing, restart your terminal and try again.",
            title="Missing Prerequisite",
            border_style="red",
        )
    )
    sys.exit(1)


def _detect_exec_prefix() -> List[str]:
    """Detect the package-manager exec prefix for running ``tauri``.

    Resolution order (based on lockfile presence):
      pnpm-lock.yaml  ->  pnpm exec tauri
      bun.lock / bun.lockb  ->  bunx tauri
      (fallback)  ->  npx tauri
    """
    cwd = Path.cwd()
    if (cwd / "pnpm-lock.yaml").exists():
        return ["pnpm", "exec"]
    if (cwd / "bun.lock").exists() or (cwd / "bun.lockb").exists():
        return ["bunx"]
    return ["npx"]


def _tauri_cmd(*args: str) -> List[str]:
    """Build the full command to run tauri with the detected package manager."""
    return [*_detect_exec_prefix(), "tauri", *args]


def _require_tauri_cli():
    """Verify @tauri-apps/cli is installed and runnable. Exit if not."""
    cmd = _tauri_cmd("--version")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    pm = _detect_exec_prefix()[0]  # pnpm / bunx / npx
    install_hint = {
        "pnpm": "pnpm install",
        "bunx": "bun install",
        "npx": "npm install",
    }.get(pm, "npm install")

    console.print(
        Panel(
            "[bold red]@tauri-apps/cli not found[/bold red]\n\n"
            "The Tauri CLI npm package is not installed.\n\n"
            f"[bold]Install it:[/bold]\n"
            f"  {install_hint}\n\n"
            "If this is a new project, run [cyan]iblai builds init[/cyan] first,\n"
            "then install dependencies.",
            title="Missing Dependency",
            border_style="red",
        )
    )
    sys.exit(1)


def _passthrough(args: Tuple[str, ...]):
    """Check prerequisites and forward args to the tauri CLI."""
    _require_rust()
    _require_tauri_cli()
    cmd = _tauri_cmd(*args)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# CLI command group
# ---------------------------------------------------------------------------

_HELP = """\
Tauri v2 build and development commands.

Thin wrapper around @tauri-apps/cli (installed via npm/pnpm/bun).
All arguments are passed directly to tauri unless the subcommand
is handled by iblai (init, ci-workflow).

Requires: Rust toolchain (rustc + cargo).  Install from https://rustup.rs

Package manager detection (by lockfile):
  pnpm-lock.yaml  ->  pnpm exec tauri ...
  bun.lock         ->  bunx tauri ...
  (fallback)       ->  npx tauri ...

iblai-managed commands:
  iblai builds init                     Add Tauri to current project
  iblai builds generate-icons <source>  Generate all icon sizes from source image
  iblai builds ci-workflow              Generate GitHub Actions workflows

All other arguments are forwarded to tauri:
  iblai builds dev                    Start desktop dev mode
  iblai builds build [--debug]        Build desktop app for distribution
  iblai builds icon <path>            Generate all icon sizes from source image

iOS (macOS with Xcode required):
  iblai builds ios init               Initialize iOS project (run once after pnpm install)
  iblai builds ios dev                Run in iOS Simulator
  iblai builds ios dev --device       Run on connected physical device
  iblai builds ios build              Build iOS app (.ipa)

Android (requires Android SDK):
  iblai builds android init           Initialize Android project
  iblai builds android dev            Run on emulator or connected device
  iblai builds android build          Build Android app (.apk / .aab)

Windows MSIX:
  pnpm tauri:build:msix              Build MSIX package (x64)
  pnpm tauri:build:msix:arm64        Build MSIX package (arm64)
  pnpm tauri:setup:cert              Create dev certificate for signing (requires admin)
"""


class BuildsGroup(click.Group):
    """Custom Click group that passes unrecognised subcommands to tauri."""

    def parse_args(self, ctx, args):
        # If the first arg matches a known command (or is --help/-h),
        # let Click handle it.  Otherwise, stash everything for passthrough.
        if args and args[0] not in self.commands and args[0] not in ("--help", "-h"):
            ctx.ensure_object(dict)
            ctx.obj["passthrough_args"] = tuple(args)
            args = []
        return super().parse_args(ctx, args)

    def invoke(self, ctx):
        ctx.ensure_object(dict)
        pt = ctx.obj.get("passthrough_args")
        if pt:
            _passthrough(pt)
        else:
            return super().invoke(ctx)

    def get_help(self, ctx):
        return _HELP


@click.group(cls=BuildsGroup, invoke_without_command=True)
@click.pass_context
def builds(ctx):
    """Tauri v2 build and development commands."""
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None and not ctx.obj.get("passthrough_args"):
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# iblai-managed subcommands
# ---------------------------------------------------------------------------


@builds.command()
def init():
    """Add Tauri v2 desktop shell to the current project."""
    from iblai.generators.add_builds import AddBuildsGenerator

    root = Path.cwd()
    pkg = root / "package.json"
    if not pkg.exists():
        console.print(
            "[red]No package.json found. Run this in a Next.js project root.[/red]"
        )
        sys.exit(1)

    if (root / "src-tauri").exists():
        console.print("[yellow]src-tauri/ already exists. Skipping.[/yellow]")
        return

    gen = AddBuildsGenerator(project_root=str(root))
    created = gen.generate()

    console.print()
    console.print(
        Panel(
            "[bold green]Tauri v2 desktop shell added[/bold green]\n\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n\n"
            "[bold]Next steps:[/bold]\n"
            "  1. Install dependencies: pnpm install\n"
            "  2. Generate icons: iblai builds generate-icons path/to/logo.png\n"
            "  3. Start development: iblai builds dev\n"
            "  4. Build for distribution: iblai builds build\n\n"
            "[bold]CI/CD:[/bold]\n"
            "  iblai builds ci-workflow --desktop\n"
            "  iblai builds ci-workflow --ios\n"
            "  iblai builds ci-workflow --all",
            title="Success",
            border_style="green",
        )
    )


@builds.command("generate-icons")
@click.argument("source", type=click.Path(exists=True))
def generate_icons(source):
    """Generate all Tauri icon sizes from a source image.

    Uses ImageMagick (convert) to create RGBA icons at all required
    sizes for Tauri, MSIX, and macOS builds. Falls back to
    'tauri icon' if ImageMagick is not installed.

    \b
    Example:
        iblai builds generate-icons logo.png
        iblai builds generate-icons docs/my-icon.png
    """
    import shutil
    import subprocess

    if not Path("src-tauri").exists():
        console.print(
            "[red]No src-tauri/ directory. Run 'iblai builds init' first.[/red]"
        )
        sys.exit(1)

    icons_dir = Path("src-tauri/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Check for ImageMagick
    convert_cmd = shutil.which("convert")
    if not convert_cmd:
        console.print(
            "[yellow]ImageMagick (convert) not found. Falling back to tauri icon...[/yellow]"
        )
        _require_rust()
        _require_tauri_cli()
        cmd = _tauri_cmd("icon", source)
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    console.print(f"[cyan]Generating icons from {source}...[/cyan]")

    sizes = {
        "32x32.png": "32x32",
        "128x128.png": "128x128",
        "128x128@2x.png": "256x256",
        "icon.png": "256x256",
        "StoreLogo.png": "50x50",
        "Square44x44Logo.png": "44x44",
        "Square71x71Logo.png": "71x71",
        "Square150x150Logo.png": "150x150",
        "Square310x310Logo.png": "310x310",
        "Wide310x150Logo.png": "310x150",
    }

    for name, size in sizes.items():
        dest = icons_dir / name
        subprocess.run(
            [
                convert_cmd,
                source,
                "-resize",
                size,
                "-gravity",
                "center",
                "-background",
                "transparent",
                "-extent",
                size,
                str(dest),
            ],
            check=True,
        )
        console.print(f"  [green]{name}[/green] ({size})")

    # ICO (multi-resolution)
    subprocess.run(
        [
            convert_cmd,
            source,
            "(",
            "-clone",
            "0",
            "-resize",
            "16x16",
            "-gravity",
            "center",
            "-background",
            "transparent",
            "-extent",
            "16x16",
            ")",
            "(",
            "-clone",
            "0",
            "-resize",
            "32x32",
            "-gravity",
            "center",
            "-background",
            "transparent",
            "-extent",
            "32x32",
            ")",
            "(",
            "-clone",
            "0",
            "-resize",
            "48x48",
            "-gravity",
            "center",
            "-background",
            "transparent",
            "-extent",
            "48x48",
            ")",
            "(",
            "-clone",
            "0",
            "-resize",
            "256x256",
            "-gravity",
            "center",
            "-background",
            "transparent",
            "-extent",
            "256x256",
            ")",
            "-delete",
            "0",
            str(icons_dir / "icon.ico"),
        ],
        check=True,
    )
    console.print("  [green]icon.ico[/green] (multi-resolution)")

    # ICNS (wrap 128x128 PNG with Python)
    png_128 = icons_dir / "128x128.png"
    if png_128.exists():
        from iblai.generators.add_builds import _create_icns

        (icons_dir / "icon.icns").write_bytes(_create_icns(png_128.read_bytes()))
        console.print("  [green]icon.icns[/green] (macOS)")

    console.print(f"\n[green]Icons generated in {icons_dir}[/green]")


@builds.command("ci-workflow")
@click.option(
    "--desktop",
    is_flag=True,
    help="Generate desktop build workflow (macOS + Linux + Windows)",
)
@click.option("--ios", "gen_ios", is_flag=True, help="Generate iOS build workflow")
@click.option(
    "--windows-msix",
    "gen_msix",
    is_flag=True,
    help="Generate Windows MSIX build workflow (x64 + arm64 + bundle)",
)
@click.option("--all", "gen_all", is_flag=True, help="Generate all platform workflows")
def ci_workflow(desktop, gen_ios, gen_msix, gen_all):
    """Generate GitHub Actions workflow files for Tauri builds."""
    from iblai.generators.add_builds import AddBuildsGenerator

    if not desktop and not gen_ios and not gen_msix and not gen_all:
        desktop = True

    root = Path.cwd()
    gen = AddBuildsGenerator(project_root=str(root))

    created = gen.generate_ci_workflows(
        desktop=desktop or gen_all,
        ios=gen_ios or gen_all,
        windows_msix=gen_msix or gen_all,
    )

    if created:
        console.print("[green]Generated CI workflows:[/green]")
        for f in created:
            console.print(f"  [cyan]{f}[/cyan]")

        if gen_ios or gen_all:
            console.print()
            console.print(
                "[yellow]iOS workflow requires these GitHub secrets:[/yellow]\n"
                "  APPLE_API_KEY_BASE64  - Base64-encoded App Store Connect API key (.p8)\n"
                "  APPLE_API_KEY_ID      - Key ID from App Store Connect\n"
                "  APPLE_API_ISSUER      - Issuer ID from App Store Connect"
            )
    else:
        console.print("[yellow]No workflows generated.[/yellow]")
