"""Generator for adding Tauri v2 desktop shell to a Next.js project."""

import json
import re
import struct
import zlib
from pathlib import Path
from typing import List

from rich.console import Console

from iblai.generators.base import BaseGenerator
from iblai.next_config_patcher import (
    find_next_config,
    patch_next_config_for_tauri,
)

console = Console()


# ---------------------------------------------------------------------------
# Pure-Python minimal icon generation (no PIL / Pillow dependency)
# ---------------------------------------------------------------------------


def _create_png(
    width: int, height: int, r: int = 59, g: int = 130, b: int = 246
) -> bytes:
    """Create a minimal valid PNG image (solid color, no transparency).

    Default color is a blue (#3B82F6) matching Tailwind's blue-500.
    """

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        """Build a PNG chunk: length + type + data + CRC32."""
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    # IHDR: width, height, bit depth 8, color type 6 (RGBA), compression 0,
    # filter 0, interlace 0
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    # IDAT: raw image data — each row starts with filter byte 0 (None),
    # followed by RGBA pixels
    raw_rows = b""
    for _ in range(height):
        raw_rows += b"\x00" + bytes([r, g, b, 255]) * width
    idat_data = zlib.compress(raw_rows)

    return (
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        + _chunk(b"IHDR", ihdr_data)
        + _chunk(b"IDAT", idat_data)
        + _chunk(b"IEND", b"")
    )


def _create_ico(png_data: bytes) -> bytes:
    """Create a minimal .ico file wrapping a single PNG image.

    ICO format: 6-byte header + 16-byte directory entry + PNG payload.
    Modern Windows (Vista+) supports PNG-compressed ICO entries.
    """
    # ICO header: reserved=0, type=1 (icon), count=1
    header = struct.pack("<HHH", 0, 1, 1)

    # Parse width/height from PNG IHDR (bytes 16-23)
    width = struct.unpack(">I", png_data[16:20])[0]
    height = struct.unpack(">I", png_data[20:24])[0]

    # ICO directory entry: width, height (0 means 256), color count, reserved,
    # planes, bit count, data size, data offset
    w = width if width < 256 else 0
    h = height if height < 256 else 0
    entry = struct.pack(
        "<BBBBHHII",
        w,  # width (0 = 256)
        h,  # height (0 = 256)
        0,  # color count (0 for truecolor)
        0,  # reserved
        1,  # color planes
        32,  # bits per pixel
        len(png_data),  # data size
        22,  # data offset (6 header + 16 entry)
    )

    return header + entry + png_data


def _create_icns(png_data: bytes) -> bytes:
    """Create a minimal .icns file wrapping a single PNG image.

    ICNS format: 4-byte magic + 4-byte total size, then entries of
    4-byte type + 4-byte size + payload.  We use 'ic07' (128x128 PNG).
    """
    icon_type = b"ic07"  # 128x128 PNG
    entry_size = 8 + len(png_data)  # type(4) + size(4) + data
    total_size = 8 + entry_size  # magic(4) + total_size(4) + entry

    return (
        b"icns"
        + struct.pack(">I", total_size)
        + icon_type
        + struct.pack(">I", entry_size)
        + png_data
    )


class AddBuildsGenerator:
    """Add Tauri v2 desktop shell to an existing Next.js project.

    Generates src-tauri/ with a minimal Tauri configuration, patches
    next.config.ts to remove @tauri-apps/api stubs and add conditional
    static export for Tauri builds, and updates package.json with Tauri
    dependencies and scripts.
    """

    def __init__(self, project_root: str, app_name: str = ""):
        self.root = Path(project_root)
        self.app_name = app_name or self._detect_app_name()
        self._generator = BaseGenerator(
            app_name=self.app_name,
            platform_key="",
            output_dir=project_root,
        )

    def _detect_app_name(self) -> str:
        """Read the app name from package.json or use directory name."""
        pkg_path = self.root / "package.json"
        if pkg_path.exists():
            try:
                data = json.loads(pkg_path.read_text(encoding="utf-8"))
                return data.get("name", self.root.name)
            except (json.JSONDecodeError, KeyError):
                pass
        return self.root.name

    def generate(self) -> List[str]:
        """Generate Tauri files and patch the project. Returns list of created/modified files."""
        created = []

        # 1. Render src-tauri/ templates
        created.extend(self._generate_src_tauri())

        # 2. Patch next.config
        patched = patch_next_config_for_tauri(self.root)
        if patched:
            created.append(patched)

        # 3. Patch package.json
        pkg_patched = self._patch_package_json()
        if pkg_patched:
            created.append("package.json")

        return created

    def _generate_src_tauri(self) -> List[str]:
        """Render all src-tauri/ files from templates."""
        created = []
        context = {
            "app_name": self.app_name,
        }

        template_map = {
            "tauri/src-tauri/tauri.conf.json.j2": "src-tauri/tauri.conf.json",
            "tauri/src-tauri/Cargo.toml.j2": "src-tauri/Cargo.toml",
            "tauri/src-tauri/src/main.rs.j2": "src-tauri/src/main.rs",
            "tauri/src-tauri/src/lib.rs.j2": "src-tauri/src/lib.rs",
            "tauri/src-tauri/capabilities/default.json.j2": "src-tauri/capabilities/default.json",
            "tauri/src-tauri/tauri.android.conf.json": "src-tauri/tauri.android.conf.json",
            "tauri/src-tauri/tauri.ios.conf.json": "src-tauri/tauri.ios.conf.json",
            "tauri/src-tauri/AppxManifest.xml.j2": "src-tauri/AppxManifest.xml",
            "tauri/src-tauri/build-msix.ps1.j2": "src-tauri/build-msix.ps1",
            "tauri/src-tauri/setup-test-cert.ps1.j2": "src-tauri/setup-test-cert.ps1",
        }

        for template_name, output_path in template_map.items():
            out = self.root / output_path
            out.parent.mkdir(parents=True, exist_ok=True)
            content = self._generator.render_template(template_name, **context)
            out.write_text(content, encoding="utf-8")
            created.append(output_path)

        # Static files (not templates)
        build_rs = self.root / "src-tauri" / "build.rs"
        build_rs.write_text(
            "fn main() {\n    tauri_build::build()\n}\n", encoding="utf-8"
        )
        created.append("src-tauri/build.rs")

        # Icons — copy pre-generated ibl.ai logo icons from templates,
        # or fall back to solid-color RGBA placeholders.
        icon_files = self._copy_icons()
        created.extend(icon_files)

        return created

    # ------------------------------------------------------------------
    # Icon handling
    # ------------------------------------------------------------------

    def _copy_icons(self) -> List[str]:
        """Copy pre-generated ibl.ai logo icons to src-tauri/icons/.

        Falls back to generating solid-color RGBA placeholders if
        the pre-generated icon templates are not available.
        """
        import shutil as _shutil

        icons_src = self._generator.template_dir / "icons"
        icons_dest = self.root / "src-tauri" / "icons"
        icons_dest.mkdir(parents=True, exist_ok=True)
        created = []

        if not icons_src.is_dir():
            # Fallback: generate solid-color RGBA placeholders
            return self._generate_placeholder_icons()

        for icon in sorted(icons_src.iterdir()):
            if icon.is_file():
                _shutil.copy2(icon, icons_dest / icon.name)
                created.append(f"src-tauri/icons/{icon.name}")

        # Generate .icns by wrapping the 128x128 RGBA PNG
        png_128 = icons_dest / "128x128.png"
        if png_128.exists():
            icns_data = _create_icns(png_128.read_bytes())
            (icons_dest / "icon.icns").write_bytes(icns_data)
            created.append("src-tauri/icons/icon.icns")

        return created

    def _generate_placeholder_icons(self) -> List[str]:
        """Fallback: create minimal RGBA placeholder icons in src-tauri/icons/."""
        icons_dir = self.root / "src-tauri" / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)
        created = []

        png_32 = _create_png(32, 32)
        png_128 = _create_png(128, 128)
        png_256 = _create_png(256, 256)

        icon_map = {
            "32x32.png": png_32,
            "128x128.png": png_128,
            "128x128@2x.png": png_256,
            "icon.png": png_256,
            "StoreLogo.png": _create_png(50, 50),
            "Square44x44Logo.png": _create_png(44, 44),
            "Square71x71Logo.png": _create_png(71, 71),
            "Square150x150Logo.png": _create_png(150, 150),
            "Square310x310Logo.png": _create_png(310, 310),
            "Wide310x150Logo.png": _create_png(310, 150),
        }

        for name, data in icon_map.items():
            (icons_dir / name).write_bytes(data)
            created.append(f"src-tauri/icons/{name}")

        (icons_dir / "icon.ico").write_bytes(_create_ico(png_32))
        created.append("src-tauri/icons/icon.ico")

        # .icns (macOS) — ICNS container wrapping a 128x128 PNG
        (icons_dir / "icon.icns").write_bytes(_create_icns(png_128))
        created.append("src-tauri/icons/icon.icns")

        return created

    def _patch_package_json(self) -> bool:
        """Add Tauri deps and scripts to package.json. Returns True if modified."""
        pkg_path = self.root / "package.json"
        if not pkg_path.exists():
            return False

        content = pkg_path.read_text(encoding="utf-8")
        data = json.loads(content)
        modified = False

        # Add dependencies
        deps = data.setdefault("dependencies", {})
        if "@tauri-apps/api" not in deps:
            deps["@tauri-apps/api"] = "^2.9.1"
            modified = True

        # Add devDependencies
        dev_deps = data.setdefault("devDependencies", {})
        if "@tauri-apps/cli" not in dev_deps:
            dev_deps["@tauri-apps/cli"] = "^2.5.0"
            modified = True

        # Add scripts
        scripts = data.setdefault("scripts", {})
        tauri_scripts = {
            "tauri": "tauri",
            "tauri:dev": "tauri dev",
            "tauri:build": "tauri build",
            "tauri:build:debug": "next build && tauri build --debug",
            "tauri:dev:android": "tauri android dev --host",
            "tauri:build:android": "tauri android build",
            "tauri:dev:ios": "tauri ios dev",
            "tauri:build:ios": "tauri ios build",
            "tauri:build:msix": "powershell -ExecutionPolicy Bypass -File src-tauri/build-msix.ps1",
            "tauri:build:msix:arm64": "powershell -ExecutionPolicy Bypass -File src-tauri/build-msix.ps1 -Architecture arm64",
            "tauri:setup:cert": "powershell -ExecutionPolicy Bypass -File src-tauri/setup-test-cert.ps1",
        }
        for key, val in tauri_scripts.items():
            if key not in scripts:
                scripts[key] = val
                modified = True

        if modified:
            pkg_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        return modified

    def generate_ci_workflows(
        self,
        desktop: bool = True,
        ios: bool = False,
        windows_msix: bool = False,
    ) -> List[str]:
        """Generate GitHub Actions workflow files for Tauri builds."""
        created = []
        context = {"app_name": self.app_name}
        workflows_dir = self.root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        if desktop:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-desktop.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-desktop.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-desktop.yml")

        if ios:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-ios.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-ios.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-ios.yml")

        if windows_msix:
            content = self._generator.render_template(
                "tauri/workflows/tauri-build-windows-msix.yml.j2", **context
            )
            out = workflows_dir / "tauri-build-windows-msix.yml"
            out.write_text(content, encoding="utf-8")
            created.append(".github/workflows/tauri-build-windows-msix.yml")

        return created
