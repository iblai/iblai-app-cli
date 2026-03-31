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

# ---------------------------------------------------------------------------
# RTK dedup — prevents duplicate @reduxjs/toolkit / react-redux copies
# ---------------------------------------------------------------------------

DEDUP_IMPORT_TS = 'import { createRequire } from "module";\n'

DEDUP_FUNCTION_TS = """\

const require = createRequire(import.meta.url);

/**
 * Resolve a package to its root directory so webpack never loads duplicate
 * copies (can happen in npm/pnpm hoisting with differing peer deps).
 * Without this, @reduxjs/toolkit may be duplicated and SDK components get
 * a different ReactReduxContext — RTK Query hooks silently return undefined.
 */
function dedup(packageName: string): string | undefined {
  try {
    const entry = require.resolve(packageName);
    const marker = `node_modules/${packageName}`;
    const idx = entry.lastIndexOf(marker);
    if (idx !== -1) return entry.slice(0, idx + marker.length);
    return undefined;
  } catch {
    return undefined;
  }
}

const resolveAliases: Record<string, string> = {};
const dataLayerDir = dedup("@iblai/data-layer");
if (dataLayerDir) resolveAliases["@iblai/data-layer"] = dataLayerDir;
const rtkDir = dedup("@reduxjs/toolkit");
if (rtkDir) resolveAliases["@reduxjs/toolkit"] = rtkDir;
const reactReduxDir = dedup("react-redux");
if (reactReduxDir) resolveAliases["react-redux"] = reactReduxDir;
"""

DEDUP_IMPORT_JS = 'import { createRequire } from "module";\n'

DEDUP_FUNCTION_JS = """\

const require = createRequire(import.meta.url);

/**
 * Resolve a package to its root directory so webpack never loads duplicate
 * copies (can happen in npm/pnpm hoisting with differing peer deps).
 * Without this, @reduxjs/toolkit may be duplicated and SDK components get
 * a different ReactReduxContext — RTK Query hooks silently return undefined.
 */
function dedup(packageName) {
  try {
    const entry = require.resolve(packageName);
    const marker = `node_modules/${packageName}`;
    const idx = entry.lastIndexOf(marker);
    if (idx !== -1) return entry.slice(0, idx + marker.length);
    return undefined;
  } catch {
    return undefined;
  }
}

const resolveAliases = {};
const dataLayerDir = dedup("@iblai/data-layer");
if (dataLayerDir) resolveAliases["@iblai/data-layer"] = dataLayerDir;
const rtkDir = dedup("@reduxjs/toolkit");
if (rtkDir) resolveAliases["@reduxjs/toolkit"] = rtkDir;
const reactReduxDir = dedup("react-redux");
if (reactReduxDir) resolveAliases["react-redux"] = reactReduxDir;
"""

DEDUP_WEBPACK_LINE = """\
    // ibl.ai: Deduplicate @reduxjs/toolkit + react-redux (shared Redux context)
    Object.assign(config.resolve.alias, resolveAliases);"""

MARKER_POLYFILL = "localStorage.getItem"
MARKER_TAURI = "@tauri-apps/api/core"
MARKER_TURBOPACK = "turbopack"
MARKER_DEDUP = "resolveAliases"
MARKER_IMAGES = "remotePatterns"

# ---------------------------------------------------------------------------
# next/image remote patterns — allows SDK components (e.g. Account) to load
# external images like org logos from api.iblai.app via next/image.
# ---------------------------------------------------------------------------

IMAGES_CONFIG = """\
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },"""

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
import { createRequire } from "module";

const require = createRequire(import.meta.url);

/**
 * Resolve a package to its root directory so webpack never loads duplicate
 * copies (can happen in npm/pnpm hoisting with differing peer deps).
 * Without this, @reduxjs/toolkit may be duplicated and SDK components get
 * a different ReactReduxContext — RTK Query hooks silently return undefined.
 */
function dedup(packageName: string): string | undefined {
  try {
    const entry = require.resolve(packageName);
    const marker = `node_modules/${packageName}`;
    const idx = entry.lastIndexOf(marker);
    if (idx !== -1) return entry.slice(0, idx + marker.length);
    return undefined;
  } catch {
    return undefined;
  }
}

const resolveAliases: Record<string, string> = {};
const dataLayerDir = dedup("@iblai/data-layer");
if (dataLayerDir) resolveAliases["@iblai/data-layer"] = dataLayerDir;
const rtkDir = dedup("@reduxjs/toolkit");
if (rtkDir) resolveAliases["@reduxjs/toolkit"] = rtkDir;
const reactReduxDir = dedup("react-redux");
if (reactReduxDir) resolveAliases["react-redux"] = reactReduxDir;

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  turbopack: {},
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = config.resolve.alias || {};
    // Deduplicate @reduxjs/toolkit + react-redux (shared Redux context)
    Object.assign(config.resolve.alias, resolveAliases);
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
    Patch or create the Next.js config with localStorage polyfill, RTK dedup,
    turbopack config, and Tauri stubs.

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

    # 2. Ensure a webpack function exists in the config object.
    #    We need it for Tauri stubs + RTK dedup aliases.
    #    Look for an existing "webpack:" property; if absent, create one.
    has_webpack = bool(re.search(r"webpack\s*:", content))
    if not has_webpack:
        export_match = re.search(r"^export\s+default", content, re.MULTILINE)
        if export_match:
            before_export = content[: export_match.start()]
            last_brace = before_export.rfind("};")
            if last_brace != -1:
                webpack_prop = (
                    "  webpack: (config) => {\n"
                    + "    config.resolve = config.resolve || {};\n"
                    + "    config.resolve.alias = config.resolve.alias || {};\n"
                    + "    return config;\n"
                    + "  },\n"
                )
                content = content[:last_brace] + webpack_prop + content[last_brace:]

    # 3. Add Tauri stubs inside the webpack function (before "return config;")
    if MARKER_TAURI not in content:
        return_match = re.search(r"^(\s*return\s+config;\s*)$", content, re.MULTILINE)
        if return_match:
            indent_line = return_match.group(0)
            content = content.replace(indent_line, TAURI_STUBS + "\n" + indent_line, 1)

    # 4. Add RTK dedup (createRequire + dedup function + resolve aliases).
    #    This prevents duplicate @reduxjs/toolkit copies which cause SDK
    #    components to use a different ReactReduxContext — RTK Query hooks
    #    silently return undefined.
    if MARKER_DEDUP not in content:
        dedup_import = DEDUP_IMPORT_TS if is_ts else DEDUP_IMPORT_JS
        dedup_fn = DEDUP_FUNCTION_TS if is_ts else DEDUP_FUNCTION_JS

        # 4a. Add createRequire import after the last import line
        if "createRequire" not in content:
            lines = content.split("\n")
            last_import_idx = -1
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("} from "):
                    last_import_idx = i
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, dedup_import.rstrip())
                content = "\n".join(lines)
            else:
                # No imports — insert after the polyfill block
                polyfill_end = content.find("}\n")
                if polyfill_end != -1:
                    insert_pos = polyfill_end + 2
                    content = (
                        content[:insert_pos]
                        + "\n"
                        + dedup_import
                        + content[insert_pos:]
                    )

        # 4b. Add the dedup function + resolveAliases before the config object
        config_obj_match = re.search(
            r"^const\s+(nextConfig|config)\s*(?::\s*\w+)?\s*=\s*\{",
            content,
            re.MULTILINE,
        )
        if config_obj_match:
            content = (
                content[: config_obj_match.start()]
                + dedup_fn
                + "\n"
                + content[config_obj_match.start() :]
            )

        # 4c. Add Object.assign(config.resolve.alias, resolveAliases)
        #     inside the webpack function, before "return config;"
        if "Object.assign(config.resolve.alias" not in content:
            return_match = re.search(
                r"^(\s*return\s+config;\s*)$", content, re.MULTILINE
            )
            if return_match:
                indent_line = return_match.group(0)
                content = content.replace(
                    indent_line,
                    DEDUP_WEBPACK_LINE + "\n" + indent_line,
                    1,
                )

    # 5. Add turbopack: {} — required by Next.js 16+ when webpack config is present.
    #    Without this, Next.js 16 errors: "This build is using Turbopack, with a
    #    `webpack` config and no `turbopack` config."
    if MARKER_TURBOPACK not in content and "webpack" in content:
        webpack_match = re.search(r"^(\s*)(webpack\s*:)", content, re.MULTILINE)
        if webpack_match:
            indent = webpack_match.group(1)
            content = content.replace(
                webpack_match.group(0),
                f"{indent}turbopack: {{}},\n{webpack_match.group(0)}",
                1,
            )

    # 6. Add images.remotePatterns — allows next/image to load external images
    #    (e.g., org logos from api.iblai.app used by the Account component).
    if MARKER_IMAGES not in content:
        # Insert before turbopack or webpack property
        turbo_match = re.search(r"^(\s*)(turbopack\s*:)", content, re.MULTILINE)
        if turbo_match:
            content = content.replace(
                turbo_match.group(0),
                IMAGES_CONFIG + "\n" + turbo_match.group(0),
                1,
            )
        else:
            webpack_match = re.search(r"^(\s*)(webpack\s*:)", content, re.MULTILINE)
            if webpack_match:
                content = content.replace(
                    webpack_match.group(0),
                    IMAGES_CONFIG + "\n" + webpack_match.group(0),
                    1,
                )
            else:
                # No turbopack or webpack — insert after opening brace of config
                config_obj_match = re.search(
                    r"(const\s+\w+\s*(?::\s*\w+)?\s*=\s*\{)",
                    content,
                )
                if config_obj_match:
                    content = content.replace(
                        config_obj_match.group(0),
                        config_obj_match.group(0) + "\n" + IMAGES_CONFIG,
                        1,
                    )

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
