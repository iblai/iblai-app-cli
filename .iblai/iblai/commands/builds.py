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


def _install_cargo_tauri():
    """Install cargo-tauri via cargo-binstall (fast) or cargo install (slow)."""
    console.print("[cyan]Installing tauri-cli via cargo...[/cyan]")
    # Try cargo-binstall first (pre-built binary, much faster)
    binstall = shutil.which("cargo-binstall")
    if binstall:
        result = subprocess.run(
            ["cargo", "binstall", "tauri-cli", "--no-confirm"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            console.print("[green]tauri-cli installed via cargo-binstall[/green]")
            return True
    # Fallback: cargo install (compiles from source)
    result = subprocess.run(
        ["cargo", "install", "tauri-cli", "--locked"],
    )
    if result.returncode == 0:
        console.print("[green]tauri-cli installed via cargo install[/green]")
        return True
    return False


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
    """Build the full command to run tauri.

    Prefers ``cargo tauri`` (installed globally via cargo-tauri),
    falling back to the JS package manager (pnpm exec / bunx / npx).
    """
    if shutil.which("cargo"):
        try:
            result = subprocess.run(
                ["cargo", "tauri", "--version"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return ["cargo", "tauri", *args]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return [*_detect_exec_prefix(), "tauri", *args]


def _require_tauri_cli():
    """Ensure a tauri CLI is available. Auto-installs via cargo if possible."""
    # Check cargo tauri first
    if shutil.which("cargo"):
        try:
            result = subprocess.run(
                ["cargo", "tauri", "--version"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # Rust available but no cargo-tauri — install it
        if _install_cargo_tauri():
            return

    # Fallback: check JS package manager
    cmd = [*_detect_exec_prefix(), "tauri", "--version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    console.print(
        Panel(
            "[bold red]Tauri CLI not found[/bold red]\n\n"
            "Install the Tauri CLI:\n\n"
            "[bold]Option A (recommended):[/bold]\n"
            "  cargo install tauri-cli --locked\n\n"
            "[bold]Option B:[/bold]\n"
            "  pnpm install  (if @tauri-apps/cli is in devDependencies)\n\n"
            "If this is a new project, run [cyan]iblai builds init[/cyan] first,\n"
            "then install dependencies.",
            title="Missing Dependency",
            border_style="red",
        )
    )
    sys.exit(1)


def _regenerate_platform_icons():
    """After ios/android init, regenerate icons from src-tauri/icons/icon.png.

    ``tauri ios init`` and ``tauri android init`` create platform asset
    catalogs with default Tauri icons.  This replaces them with the app's
    own icons by running ``cargo tauri icon``.
    """
    icon_src = Path("src-tauri/icons/icon.png")
    if not icon_src.exists():
        return
    console.print("[cyan]Updating platform icons from src-tauri/icons/icon.png...[/cyan]")
    cmd = _tauri_cmd("icon", str(icon_src))
    subprocess.run(cmd)


def _passthrough(args: Tuple[str, ...]):
    """Check prerequisites and forward args to the tauri CLI."""
    _require_rust()
    _require_tauri_cli()
    cmd = _tauri_cmd(*args)
    result = subprocess.run(cmd)
    # After ios/android init, regenerate icons so platform assets use
    # the app's icons instead of the default Tauri icon.
    if result.returncode == 0 and len(args) >= 2 and args[1] == "init":
        if args[0] in ("ios", "android"):
            _regenerate_platform_icons()
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
  iblai builds iconography <source>     Generate all icon sizes from source image
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

App store tools:
  iblai builds device                List available simulators and emulators
  iblai builds screenshot [--pages]  Generate Playwright screenshot script
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
            "  2. Generate icons: iblai builds iconography path/to/logo.png\n"
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


@builds.command("iconography")
@click.argument("source", type=click.Path(exists=True))
def generate_icons(source):
    """Generate all Tauri icon sizes from a source image.

    Uses ImageMagick (convert) to create RGBA icons at all required
    sizes for Tauri, MSIX, and macOS builds. Falls back to
    'tauri icon' if ImageMagick is not installed.

    \b
    Example:
        iblai builds iconography logo.png
        iblai builds iconography docs/my-icon.png
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
                "none",
                "-extent",
                size,
                "-alpha",
                "on",
                f"PNG32:{dest}",
            ],
            check=True,
        )
        console.print(f"  [green]{name}[/green] ({size})")

    # ICO (multi-resolution)
    subprocess.run(
        [
            convert_cmd,
            source,
            "-alpha",
            "on",
            "(",
            "-clone",
            "0",
            "-resize",
            "16x16",
            "-gravity",
            "center",
            "-background",
            "none",
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
            "none",
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
            "none",
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
            "none",
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


# ---------------------------------------------------------------------------
# iblai builds device — list available simulators/emulators/devices
# ---------------------------------------------------------------------------


@builds.command("device")
def devices():
    """List available iOS simulators, Android emulators, and physical devices."""
    import json
    import os
    import platform
    import shutil
    import subprocess

    from rich.table import Table as RichTable

    table = RichTable(
        title="Available Devices",
        show_lines=True,
        border_style="blue",
    )
    table.add_column("Platform", style="bold", min_width=12)
    table.add_column("Device", min_width=22)
    table.add_column("Version", min_width=10)
    table.add_column("Status", min_width=10)
    table.add_column("UDID", style="dim", min_width=16)

    found = False

    # --- iOS Simulators (macOS only) ---
    if platform.system() == "Darwin" and shutil.which("xcrun"):
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for runtime, device_list in data.get("devices", {}).items():
                    # runtime looks like "com.apple.CoreSimulator.SimRuntime.iOS-18-0"
                    version = runtime.split(".")[-1].replace("-", ".")
                    if (
                        "iOS" not in runtime
                        and "watchOS" not in runtime
                        and "tvOS" not in runtime
                    ):
                        continue
                    for dev in device_list:
                        if not dev.get("isAvailable", False):
                            continue
                        state = dev.get("state", "Unknown")
                        style = "green" if state == "Booted" else ""
                        table.add_row(
                            "iOS Sim",
                            dev.get("name", "Unknown"),
                            version,
                            f"[{style}]{state}[/{style}]" if style else state,
                            dev.get("udid", ""),
                        )
                        found = True
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass

    # --- Android Emulators ---
    emulator_cmd = shutil.which("emulator")
    if not emulator_cmd:
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get(
            "ANDROID_SDK_ROOT"
        )
        if android_home:
            candidate = Path(android_home) / "emulator" / "emulator"
            if candidate.exists():
                emulator_cmd = str(candidate)

    if emulator_cmd:
        try:
            result = subprocess.run(
                [emulator_cmd, "-list-avds"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for avd in result.stdout.strip().splitlines():
                    avd = avd.strip()
                    if avd:
                        # Extract API level from AVD name if possible
                        api = ""
                        for part in avd.split("_"):
                            if part.startswith("API"):
                                api = f"API {part[3:]}"
                        table.add_row("Android Emu", avd, api or "—", "Offline", avd)
                        found = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # --- Physical iOS devices (macOS only) ---
    if platform.system() == "Darwin" and shutil.which("xcrun"):
        try:
            result = subprocess.run(
                ["xcrun", "xctrace", "list", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                in_devices = False
                for line in result.stdout.splitlines():
                    if "== Devices ==" in line:
                        in_devices = True
                        continue
                    if "== Simulators ==" in line:
                        break
                    if in_devices and line.strip():
                        # Format: "Device Name (version) (UDID)"
                        line = line.strip()
                        # Skip "This Mac" entries
                        if "This Mac" in line or "Mac" in line.split("(")[0]:
                            continue
                        parts = line.rsplit("(", 2)
                        if len(parts) >= 3:
                            name = parts[0].strip()
                            version = parts[1].rstrip(")").strip()
                            udid = parts[2].rstrip(")").strip()
                            table.add_row(
                                "Physical",
                                name,
                                version,
                                "[green]Connected[/green]",
                                udid,
                            )
                            found = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # --- Physical Android devices ---
    if shutil.which("adb"):
        try:
            result = subprocess.run(
                ["adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines()[1:]:
                    line = line.strip()
                    if not line or "offline" in line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] in ("device", "unauthorized"):
                        serial = parts[0]
                        # Extract model from properties
                        model = serial
                        for part in parts[2:]:
                            if part.startswith("model:"):
                                model = part.split(":")[1]
                                break
                        status = (
                            "[green]Connected[/green]"
                            if parts[1] == "device"
                            else "[yellow]Unauthorized[/yellow]"
                        )
                        table.add_row("Physical", model, "—", status, serial)
                        found = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if found:
        console.print()
        console.print(table)
        console.print()
    else:
        console.print("[yellow]No devices found.[/yellow]\n")
        if platform.system() == "Darwin":
            console.print(
                "  iOS Simulators: Open Xcode → Settings → Platforms → Download simulators"
            )
        console.print("  Android Emulators: Install Android Studio → AVD Manager")
        console.print("  Physical devices: Connect via USB or wireless ADB")


# ---------------------------------------------------------------------------
# iblai builds screenshot — generate Playwright screenshot script
# ---------------------------------------------------------------------------


SCREENSHOTS_SCRIPT = """\
import {{ test }} from "@playwright/test";

const BASE_URL = process.env.SCREENSHOT_BASE_URL || "{base_url}";

const VIEWPORTS = {{
  "iPhone 6.7\\"": {{ width: 430, height: 932 }},
  "iPhone 6.1\\"": {{ width: 390, height: 844 }},
  "iPad 12.9\\"": {{ width: 1024, height: 1366 }},
  "Android Phone": {{ width: 412, height: 915 }},
  "Android Tablet": {{ width: 800, height: 1280 }},
  "Apple Watch 49mm": {{ width: 205, height: 251 }},
  "Apple Watch 45mm": {{ width: 198, height: 242 }},
  "Desktop": {{ width: 1440, height: 900 }},
}};

const PAGES = [
{pages_entries}
];

function slug(s: string): string {{
  return s.replace(/[^a-zA-Z0-9]/g, "-").toLowerCase();
}}

for (const [device, viewport] of Object.entries(VIEWPORTS)) {{
  test.describe(device, () => {{
    test.use({{ viewport }});

    for (const page of PAGES) {{
      test(page.name, async ({{ page: p }}) => {{
        await p.goto(`${{BASE_URL}}${{page.path}}`);
        await p.waitForTimeout(2000);
        await p.screenshot({{
          path: `{output_dir}/${{slug(device)}}/${{page.name}}.png`,
          fullPage: false,
        }});
      }});
    }}
  }});
}}
"""


@builds.command("screenshot")
@click.option(
    "--pages",
    multiple=True,
    default=["/", "/sso-login-complete"],
    help="Paths to capture (default: / /sso-login-complete). Repeat for multiple.",
)
@click.option(
    "--url",
    default="http://localhost:3000",
    help="Base URL (default: http://localhost:3000, or SCREENSHOT_BASE_URL env var).",
)
@click.option(
    "--output",
    "output_dir",
    default="screenshots",
    help="Output directory for screenshots (default: screenshots/).",
)
def screenshots(pages, url, output_dir):
    """Generate a Playwright script for capturing app store screenshots.

    \b
    Generates e2e/screenshots.spec.ts with test.describe groups for each
    device viewport (iPhone, iPad, Android, Watch, Desktop).

    \b
    Examples:
      iblai builds screenshot
      iblai builds screenshot --pages / /profile /notifications
      iblai builds screenshot --url https://staging.myapp.com
    """
    e2e_dir = Path("e2e")
    e2e_dir.mkdir(parents=True, exist_ok=True)

    output_file = e2e_dir / "screenshots.spec.ts"

    # Build the PAGES entries
    pages_lines = []
    for page_path in pages:
        name = page_path.strip("/").replace("/", "-") or "home"
        pages_lines.append(f'  {{ name: "{name}", path: "{page_path}" }},')
    pages_entries = "\n".join(pages_lines)

    # Generate the script
    script = SCREENSHOTS_SCRIPT.format(
        base_url=url,
        pages_entries=pages_entries,
        output_dir=output_dir,
    )

    existed = output_file.exists()
    output_file.write_text(script, encoding="utf-8")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(
        Panel(
            "[bold green]Screenshot script generated[/bold green]\n\n"
            f"[bold]File:[/bold] {output_file}\n"
            + ("[dim](overwritten)[/dim]\n" if existed else "\n")
            + f"[bold]Viewports:[/bold] 8 (iPhone, iPad, Android, Watch, Desktop)\n"
            f"[bold]Pages:[/bold] {', '.join(pages)}\n"
            f"[bold]Output:[/bold] {output_dir}/\n\n"
            "[bold]Run the capture:[/bold]\n"
            "  1. Start the dev server: pnpm dev\n"
            f"  2. pnpm exec playwright test {output_file}\n\n"
            "[bold]Custom base URL:[/bold]\n"
            f"  SCREENSHOT_BASE_URL=https://staging.example.com \\\n"
            f"    pnpm exec playwright test {output_file}",
            border_style="green",
            title="iblai builds screenshot",
        )
    )
