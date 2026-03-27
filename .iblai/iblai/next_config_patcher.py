"""Patch next.config.{ts,mjs,js}, globals.css, and .env.local for ibl.ai integration."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

console = Console()

# ---------------------------------------------------------------------------
# localStorage polyfill (Node.js 22+)
# ---------------------------------------------------------------------------

LOCALSTORAGE_POLYFILL = """\
// ibl.ai: Node.js 22+ localStorage polyfill (missing getItem/setItem in SSR)
if (typeof window === "undefined" && typeof localStorage !== "undefined" && typeof localStorage.getItem !== "function") {
  const _s: Record<string, string> = {};
  globalThis.localStorage = {
    getItem: (k: string) => (_s[k] ?? null),
    setItem: (k: string, v: string) => { _s[k] = String(v); },
    removeItem: (k: string) => { delete _s[k]; },
    clear: () => { for (const k in _s) delete _s[k]; },
    get length() { return Object.keys(_s).length; },
    key: (i: number) => Object.keys(_s)[i] ?? null,
  } as Storage;
}
"""

LOCALSTORAGE_POLYFILL_JS = """\
// ibl.ai: Node.js 22+ localStorage polyfill (missing getItem/setItem in SSR)
if (typeof window === "undefined" && typeof localStorage !== "undefined" && typeof localStorage.getItem !== "function") {
  const _s = {};
  globalThis.localStorage = {
    getItem: (k) => (_s[k] ?? null),
    setItem: (k, v) => { _s[k] = String(v); },
    removeItem: (k) => { delete _s[k]; },
    clear: () => { for (const k in _s) delete _s[k]; },
    get length() { return Object.keys(_s).length; },
    key: (i) => Object.keys(_s)[i] ?? null,
  };
}
"""

# ---------------------------------------------------------------------------
# Tauri stub aliases
# ---------------------------------------------------------------------------

TAURI_STUBS = """\
    // ibl.ai: Stub @tauri-apps/api imports (not needed for web-only apps)
    config.resolve.alias["@tauri-apps/api/core"] = false;
    config.resolve.alias["@tauri-apps/api/event"] = false;"""

MARKER_POLYFILL = "localStorage.getItem"
MARKER_TAURI = "@tauri-apps/api/core"

# ---------------------------------------------------------------------------
# Default next.config.ts content (when none exists)
# ---------------------------------------------------------------------------

DEFAULT_NEXT_CONFIG_TS = """\
// ibl.ai: Node.js 22+ localStorage polyfill (missing getItem/setItem in SSR)
if (typeof window === "undefined" && typeof localStorage !== "undefined" && typeof localStorage.getItem !== "function") {
  const _s: Record<string, string> = {};
  globalThis.localStorage = {
    getItem: (k: string) => (_s[k] ?? null),
    setItem: (k: string, v: string) => { _s[k] = String(v); },
    removeItem: (k: string) => { delete _s[k]; },
    clear: () => { for (const k in _s) delete _s[k]; },
    get length() { return Object.keys(_s).length; },
    key: (i: number) => Object.keys(_s)[i] ?? null,
  } as Storage;
}

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config) => {
    // Stub @tauri-apps/api imports (not needed for web-only apps)
    config.resolve.alias["@tauri-apps/api/core"] = false;
    config.resolve.alias["@tauri-apps/api/event"] = false;
    return config;
  },
};

export default nextConfig;
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_next_config(root: Path) -> Optional[Path]:
    """Find next.config.ts, .mjs, or .js (in that priority order)."""
    for name in ("next.config.ts", "next.config.mjs", "next.config.js"):
        p = root / name
        if p.exists():
            return p
    return None


def patch_next_config(root: Path) -> str:
    """
    Patch or create the Next.js config with Tauri stubs + localStorage polyfill.

    Returns the relative path of the config file that was created or patched.
    """
    config_path = find_next_config(root)

    if config_path is None:
        # No config file exists — create next.config.ts
        config_path = root / "next.config.ts"
        config_path.write_text(DEFAULT_NEXT_CONFIG_TS, encoding="utf-8")
        return "next.config.ts"

    content = config_path.read_text(encoding="utf-8")
    original = content
    is_ts = config_path.suffix == ".ts"

    # 1. Add localStorage polyfill at the top (before first import/const)
    if MARKER_POLYFILL not in content:
        polyfill = LOCALSTORAGE_POLYFILL if is_ts else LOCALSTORAGE_POLYFILL_JS
        # Insert before the first import or const statement
        match = re.search(r"^(import |const |export |/\*\*)", content, re.MULTILINE)
        if match:
            content = (
                content[: match.start()] + polyfill + "\n" + content[match.start() :]
            )
        else:
            content = polyfill + "\n" + content

    # 2. Add Tauri stubs inside the webpack function
    if MARKER_TAURI not in content:
        # Look for "return config;" or "return nextConfig;" inside a webpack function
        return_match = re.search(r"^(\s*return\s+\w+;\s*)$", content, re.MULTILINE)
        if return_match:
            indent_line = return_match.group(0)
            content = content.replace(indent_line, TAURI_STUBS + "\n" + indent_line, 1)
        else:
            # No webpack function found — try to add one to the config object
            # Look for the config object closing: "};", preceded by the config variable
            config_var_match = re.search(r"const\s+(nextConfig|config)\b", content)
            config_var = config_var_match.group(1) if config_var_match else "nextConfig"

            # Find the last "};" before "export default"
            export_match = re.search(r"^export\s+default", content, re.MULTILINE)
            if export_match:
                # Insert webpack property before the closing of the config object
                # Find the "};" that comes right before the export
                before_export = content[: export_match.start()]
                last_brace = before_export.rfind("};")
                if last_brace != -1:
                    webpack_prop = (
                        "  webpack: (config) => {\n"
                        + TAURI_STUBS
                        + "\n"
                        + "    return config;\n"
                        + "  },\n"
                    )
                    content = content[:last_brace] + webpack_prop + content[last_brace:]

    if content != original:
        config_path.write_text(content, encoding="utf-8")

    return str(config_path.relative_to(root))


def patch_globals_css(root: Path, app_dir: Path) -> Optional[str]:
    """
    Prepend ``@import './iblai-styles.css';`` to globals.css if not present.

    Returns the relative path of the patched file, or None if not found.
    """
    for name in ("globals.css", "global.css"):
        css_path = app_dir / name
        if css_path.exists():
            content = css_path.read_text(encoding="utf-8")
            import_line = "@import './iblai-styles.css';"
            if import_line not in content and "iblai-styles.css" not in content:
                # Insert after existing @import lines, or at the very top
                # Find the last @import line
                lines = content.split("\n")
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("@import"):
                        insert_idx = i + 1
                lines.insert(insert_idx, import_line)
                css_path.write_text("\n".join(lines), encoding="utf-8")
            return str(css_path.relative_to(root))
    return None


def write_env_local(root: Path, env_vars: Dict[str, str]) -> str:
    """
    Create or append ibl.ai env vars to .env.local.

    Skips keys that already exist in the file. Returns ``".env.local"``.
    """
    path = root / ".env.local"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    lines_to_add: List[str] = []
    for key, value in env_vars.items():
        if key not in existing:
            lines_to_add.append(f"{key}={value}")

    if lines_to_add:
        separator = "\n" if existing and not existing.endswith("\n") else ""
        header = (
            "# ibl.ai Configuration\n" if not existing else "\n# ibl.ai Configuration\n"
        )
        with open(path, "a", encoding="utf-8") as f:
            f.write(separator + header + "\n".join(lines_to_add) + "\n")

    return ".env.local"


def patch_store_for_chat(root: Path, store_dir: Path) -> Optional[str]:
    """
    Add ``chatSliceReducerShared`` and ``filesReducer`` to the Redux store.

    Searches for ``store/index.ts`` or ``store/iblai-store.ts``, then injects
    the web-utils import and two reducer entries.  Idempotent — skips if the
    slices are already present.  Returns the relative path of the patched
    file, or ``None`` if no store was found or it was already patched.
    """
    for name in ("index.ts", "iblai-store.ts"):
        store_path = store_dir / name
        if not store_path.exists():
            continue

        content = store_path.read_text(encoding="utf-8")

        # Already patched?
        if "chatSliceReducerShared" in content:
            return None

        original = content

        # 1. Add the web-utils import after the last existing import
        web_utils_import = (
            "import {\n"
            "  chatSliceReducerShared,\n"
            "  filesReducer,\n"
            '} from "@iblai/iblai-js/web-utils";\n'
        )
        if "@iblai/iblai-js/web-utils" not in content:
            # Find the last import line and insert after it
            lines = content.split("\n")
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "} from "
                ):
                    last_import_idx = i
            lines.insert(last_import_idx + 1, web_utils_import)
            content = "\n".join(lines)

        # 2. Add reducer entries — insert after the coreApiSlice reducer line
        reducer_lines = (
            "    chatSliceShared: chatSliceReducerShared,\n    files: filesReducer,"
        )
        if "coreApiSlice.reducerPath" in content:
            content = content.replace(
                "[coreApiSlice.reducerPath]: coreApiSlice.reducer,",
                "[coreApiSlice.reducerPath]: coreApiSlice.reducer,\n" + reducer_lines,
                1,
            )

        if content != original:
            store_path.write_text(content, encoding="utf-8")
            return str(store_path.relative_to(root))

    return None


# ---------------------------------------------------------------------------
# Tauri-specific patching
# ---------------------------------------------------------------------------

MARKER_TAURI_EXPORT = 'output: "export"'

TAURI_EXPORT_CONFIG = """\
  // Tauri: static export to ./out for desktop/mobile builds
  output: "export",
  images: {
    unoptimized: true,
    remotePatterns: [{ protocol: 'https', hostname: '**' }],
  },"""


def patch_next_config_for_tauri(root: Path) -> Optional[str]:
    """
    Patch next.config for Tauri: remove @tauri-apps/api stubs and add
    conditional output: "export" for Tauri builds.

    Returns the relative path of the patched file, or None if nothing changed.
    """
    config_path = find_next_config(root)
    if config_path is None:
        return None

    content = config_path.read_text(encoding="utf-8")
    original = content

    # 1. Remove @tauri-apps/api stubs (they were only for web-only apps)
    #    These lines set the alias to `false` to suppress import errors.
    #    With Tauri installed, the real package is available.
    stub_patterns = [
        r"\s*//.*Stub.*@tauri-apps.*\n",
        r"\s*//.*IBL\.ai:.*Stub.*@tauri-apps.*\n",
        r"\s*//.*@tauri-apps/api is installed.*\n",
        r"\s*config\.resolve\.alias\[.*@tauri-apps/api/core.*\]\s*=\s*false;\n",
        r"\s*config\.resolve\.alias\[.*@tauri-apps/api/event.*\]\s*=\s*false;\n",
    ]
    for pat in stub_patterns:
        content = re.sub(pat, "", content)

    # 2. Add conditional export config for Tauri builds
    if MARKER_TAURI_EXPORT not in content:
        # Insert after "reactStrictMode: true," or at the start of the config object
        strict_match = re.search(r"(reactStrictMode:\s*true,)", content)
        if strict_match:
            content = content.replace(
                strict_match.group(0),
                strict_match.group(0) + "\n" + TAURI_EXPORT_CONFIG,
                1,
            )
        else:
            # Find the opening of the config object: "const nextConfig = {"
            obj_match = re.search(r"(const\s+\w+\s*(?::\s*\w+)?\s*=\s*\{)", content)
            if obj_match:
                content = content.replace(
                    obj_match.group(0),
                    obj_match.group(0) + "\n" + TAURI_EXPORT_CONFIG,
                    1,
                )

    if content != original:
        config_path.write_text(content, encoding="utf-8")
        return str(config_path.relative_to(root))

    return None
