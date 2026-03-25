"""iblai tauri — Tauri v2 build and development commands.

Wraps cargo tauri with prerequisite checking, auto-installation
of tauri-cli, and platform-specific guidance.
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


# ---------------------------------------------------------------------------
# Prerequisite helpers
# ---------------------------------------------------------------------------


def _has_rust() -> bool:
    """Check if rustc and cargo are available."""
    return shutil.which("rustc") is not None and shutil.which("cargo") is not None


def _has_tauri_cli() -> bool:
    """Check if cargo-tauri is installed."""
    try:
        result = subprocess.run(
            ["cargo", "tauri", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _require_rust():
    """Exit with a helpful message if Rust is not installed."""
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


def _ensure_tauri_cli():
    """Install tauri-cli if not present. Requires Rust to be installed."""
    if _has_tauri_cli():
        return

    console.print("[yellow]Installing tauri-cli...[/yellow]")

    # Try cargo-binstall first (pre-compiled, ~10x faster than compiling)
    binstall_ok = False
    if shutil.which("cargo-binstall"):
        try:
            subprocess.run(
                ["cargo", "binstall", "tauri-cli", "--no-confirm"],
                check=True,
                timeout=120,
            )
            binstall_ok = True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

    if not binstall_ok:
        # Try installing cargo-binstall first, then tauri-cli
        try:
            console.print("[dim]Trying cargo-binstall for faster install...[/dim]")
            subprocess.run(
                ["cargo", "install", "cargo-binstall", "--locked"],
                check=True,
                capture_output=True,
                timeout=300,
            )
            subprocess.run(
                ["cargo", "binstall", "tauri-cli", "--no-confirm"],
                check=True,
                timeout=120,
            )
            binstall_ok = True
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            pass

    if not binstall_ok:
        # Fallback: compile from source (slow but always works)
        console.print(
            "[dim]Compiling tauri-cli from source (this may take a few minutes)...[/dim]"
        )
        try:
            subprocess.run(
                ["cargo", "install", "tauri-cli", "--locked"],
                check=True,
                timeout=600,
            )
        except subprocess.CalledProcessError:
            console.print("[red]Failed to install tauri-cli. Try manually:[/red]")
            console.print("  cargo install tauri-cli --locked")
            sys.exit(1)

    console.print("[green]tauri-cli installed successfully[/green]")


def _require_src_tauri():
    """Exit if src-tauri/ doesn't exist."""
    if not Path("src-tauri").exists():
        console.print(
            "[red]No src-tauri/ directory found.[/red]\n"
            "Run [cyan]iblai tauri init[/cyan] or [cyan]iblai add tauri[/cyan] first."
        )
        sys.exit(1)


def _require_macos(feature: str):
    """Exit if not running on macOS."""
    if platform.system() != "Darwin":
        console.print(
            Panel(
                f"[bold red]{feature} requires macOS with Xcode[/bold red]\n\n"
                "Apple only allows building iOS apps on macOS.\n\n"
                "[bold]Options:[/bold]\n"
                "  1. Run this command on a Mac\n"
                "  2. Use CI: [cyan]iblai tauri ci-workflow --ios[/cyan]\n"
                "     Generates a GitHub Actions workflow that builds on macos-latest",
                title="Platform Requirement",
                border_style="red",
            )
        )
        sys.exit(1)


def _require_xcode():
    """Exit if xcodebuild is not available."""
    if not shutil.which("xcodebuild"):
        console.print(
            "[red]Xcode not found.[/red]\n"
            "Install Xcode from the Mac App Store, then run:\n"
            "  xcode-select --install"
        )
        sys.exit(1)


def _require_android_sdk():
    """Exit if Android SDK is not available."""
    import os

    if not os.environ.get("ANDROID_HOME") and not os.environ.get("ANDROID_SDK_ROOT"):
        console.print(
            "[red]Android SDK not found.[/red]\n"
            "Set ANDROID_HOME or install Android Studio.\n"
            "See: [cyan]https://developer.android.com/studio[/cyan]"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI command group
# ---------------------------------------------------------------------------


@click.group()
def tauri():
    """Tauri v2 desktop/mobile build and development commands."""
    pass


@tauri.command()
def init():
    """Add Tauri v2 desktop shell to the current project."""
    from iblai_cli.generators.add_tauri import AddTauriGenerator

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

    gen = AddTauriGenerator(project_root=str(root))
    created = gen.generate()

    console.print()
    console.print(
        Panel(
            "[bold green]Tauri v2 desktop shell added[/bold green]\n\n"
            + "\n".join(f"  [cyan]{f}[/cyan]" for f in created)
            + "\n\n"
            "[bold]Next steps:[/bold]\n"
            "  1. Install dependencies: pnpm install\n"
            "  2. Generate icons: cargo tauri icon path/to/icon.png\n"
            "  3. Start development: iblai tauri dev\n"
            "  4. Build for distribution: iblai tauri build",
            title="Success",
            border_style="green",
        )
    )


@tauri.command()
def dev():
    """Start Tauri development mode (Next.js dev server + native shell)."""
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    console.print("[cyan]Starting Tauri development mode...[/cyan]")
    subprocess.run(["cargo", "tauri", "dev"], check=False)


@tauri.command()
@click.option(
    "--debug", is_flag=True, help="Build in debug mode (faster, larger binary)"
)
def build(debug):
    """Build Tauri app for the current platform."""
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    cmd = ["cargo", "tauri", "build"]
    if debug:
        cmd.append("--debug")

    console.print(
        f"[cyan]Building Tauri app ({'debug' if debug else 'release'})...[/cyan]"
    )
    subprocess.run(cmd, check=False)


@tauri.command()
@click.argument("image_path", type=click.Path(exists=True))
def icon(image_path):
    """Generate all icon sizes from a source image."""
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    console.print(f"[cyan]Generating icons from {image_path}...[/cyan]")
    subprocess.run(["cargo", "tauri", "icon", image_path], check=False)


# ---------------------------------------------------------------------------
# iOS subcommands
# ---------------------------------------------------------------------------


@tauri.group()
def ios():
    """iOS build and development commands (macOS only)."""
    pass


@ios.command("init")
def ios_init():
    """Initialize iOS project (generates Xcode project)."""
    _require_macos("iOS builds")
    _require_xcode()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    console.print("[cyan]Initializing iOS project...[/cyan]")
    subprocess.run(["cargo", "tauri", "ios", "init"], check=False)


@ios.command("dev")
@click.option("--device", is_flag=True, help="Run on a connected physical device")
def ios_dev(device):
    """Run in iOS Simulator (or physical device with --device)."""
    _require_macos("iOS development")
    _require_xcode()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    cmd = ["cargo", "tauri", "ios", "dev"]
    if device:
        cmd.append("--device")

    console.print("[cyan]Starting iOS development mode...[/cyan]")
    subprocess.run(cmd, check=False)


@ios.command("build")
@click.option(
    "--export-method",
    type=click.Choice(["app-store-connect", "ad-hoc", "development"]),
    help="Export method for the IPA",
)
def ios_build(export_method):
    """Build iOS app (.ipa)."""
    _require_macos("iOS builds")
    _require_xcode()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    cmd = ["cargo", "tauri", "ios", "build"]
    if export_method:
        cmd.extend(["--export-method", export_method])

    console.print("[cyan]Building iOS app...[/cyan]")
    subprocess.run(cmd, check=False)


# ---------------------------------------------------------------------------
# Android subcommands
# ---------------------------------------------------------------------------


@tauri.group()
def android():
    """Android build and development commands."""
    pass


@android.command("init")
def android_init():
    """Initialize Android project."""
    _require_android_sdk()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    console.print("[cyan]Initializing Android project...[/cyan]")
    subprocess.run(["cargo", "tauri", "android", "init"], check=False)


@android.command("dev")
def android_dev():
    """Run on Android emulator or connected device."""
    _require_android_sdk()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    console.print("[cyan]Starting Android development mode...[/cyan]")
    subprocess.run(["cargo", "tauri", "android", "dev"], check=False)


@android.command("build")
@click.option("--debug", is_flag=True, help="Build in debug mode")
def android_build(debug):
    """Build Android app (.apk / .aab)."""
    _require_android_sdk()
    _require_rust()
    _ensure_tauri_cli()
    _require_src_tauri()

    cmd = ["cargo", "tauri", "android", "build"]
    if debug:
        cmd.append("--debug")

    console.print("[cyan]Building Android app...[/cyan]")
    subprocess.run(cmd, check=False)


# ---------------------------------------------------------------------------
# CI workflow generation
# ---------------------------------------------------------------------------


@tauri.command("ci-workflow")
@click.option(
    "--desktop",
    is_flag=True,
    help="Generate desktop build workflow (macOS + Linux + Windows)",
)
@click.option("--ios", "gen_ios", is_flag=True, help="Generate iOS build workflow")
@click.option("--all", "gen_all", is_flag=True, help="Generate all platform workflows")
def ci_workflow(desktop, gen_ios, gen_all):
    """Generate GitHub Actions workflow files for Tauri builds."""
    from iblai_cli.generators.add_tauri import AddTauriGenerator

    if not desktop and not gen_ios and not gen_all:
        # Default to desktop
        desktop = True

    root = Path.cwd()
    gen = AddTauriGenerator(project_root=str(root))

    created = gen.generate_ci_workflows(
        desktop=desktop or gen_all,
        ios=gen_ios or gen_all,
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
