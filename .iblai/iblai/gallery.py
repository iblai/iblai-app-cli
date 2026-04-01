"""Parse @iblai/web-containers .d.ts files and generate a component gallery.

Fetches the latest npm tarball, extracts type declaration files, parses
all named exports, categorizes them, and generates a markdown gallery
section suitable for embedding in a SKILL.md file.

Optionally scaffolds a temp Next.js app, renders components, and takes
Playwright screenshots (``--screenshots`` flag on the CLI).
"""

import io
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NPM_REGISTRY_URL = "https://registry.npmjs.org/@iblai/web-containers/latest"
REQUEST_TIMEOUT = 30

# Tarball member paths for the three entry-point .d.ts files.
ENTRY_POINTS: Dict[str, str] = {
    ".": "package/dist/index.d.ts",
    "./next": "package/dist/next/index.d.ts",
    "./sso": "package/dist/sso/index.d.ts",
}

# Consumer-facing import prefix (re-exported through @iblai/iblai-js).
IMPORT_PREFIX = "@iblai/iblai-js/web-containers"

# Section markers in the SKILL.md.
START_MARKER = "## Component Gallery"
END_MARKER = "## Component Priority"

# GitHub raw URL base for screenshot images.
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/iblai/vibe/"
    "refs/heads/main/skills/iblai-components"
)

# Pages to screenshot: (category_key, route, filename)
SCREENSHOT_PAGES = [
    ("mentor", "/", "gallery-mentor.png"),
    ("auth", "__login__", "gallery-auth.png"),
    ("profile", "/profile", "gallery-profile.png"),
    ("profile", "/account", "gallery-account.png"),
    ("analytics", "/analytics", "gallery-analytics.png"),
    ("notifications", "/notifications", "gallery-notifications.png"),
    ("errors", "/error-demo", "gallery-errors.png"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExportEntry:
    """A single named export from a .d.ts file."""

    name: str
    subpath: str  # ".", "./next", or "./sso"
    import_path: str  # e.g. "@iblai/iblai-js/web-containers/next"
    kind: str  # component, function, const, type, interface, enum, unknown


@dataclass
class CategoryDef:
    """Definition of a gallery category."""

    title: str
    entries: List[ExportEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Component mapping  (name -> (category_key, description))
# ---------------------------------------------------------------------------

COMPONENT_MAP: Dict[str, Tuple[str, str]] = {
    # --- Authentication & SSO ---
    "SsoLogin": (
        "auth",
        "SSO callback handler -- stores tokens from URL into localStorage and redirects",
    ),
    "LoginButton": (
        "auth",
        "Auth login button -- redirects to `authUrl` with redirect options",
    ),
    "SignupButton": (
        "auth",
        "Signup button -- opens signup flow, optionally in new tab",
    ),
    "handleSsoCallback": ("auth", "Process SSO callback response"),
    "parseSsoData": ("auth", "Parse SSO authentication data"),
    "initializeLocalStorageWithObject": (
        "auth",
        "Initialize localStorage from SSO data object",
    ),
    "DEFAULT_SSO_STORAGE_KEYS": ("auth", "Default localStorage key constants for SSO"),
    "getBaseDomain": ("auth", "Extract base domain from hostname"),
    "setCookie": ("auth", "Set a cookie with domain and expiry"),
    "syncSsoDataToCookies": ("auth", "Sync SSO session data to cookies"),
    # --- User Profile & Account ---
    "UserProfileDropdown": (
        "profile",
        "Avatar dropdown with profile link, tenant switcher, logout",
    ),
    "UserProfileModal": (
        "profile",
        "Profile editing modal with tabs (Basic, Social, Education, Experience, Resume, Security)",
    ),
    "Profile": ("profile", "Full profile management component"),
    "Account": (
        "profile",
        "Account/org settings with tabs (Organization, Management, Integrations, Advanced, Billing)",
    ),
    "OrganizationTab": ("profile", "Organization settings tab"),
    "InviteUserDialog": ("profile", "Dialog to invite users to a tenant"),
    "InvitedUsersDialog": ("profile", "Dialog showing pending invitations"),
    "EducationTab": ("profile", "Education background management"),
    "ExperienceTab": ("profile", "Professional experience management"),
    "ResumeTab": ("profile", "Resume upload and display"),
    "EducationDialog": ("profile", "Dialog for adding/editing education"),
    "ExperienceDialog": ("profile", "Dialog for adding/editing experience"),
    "InstitutionDialog": ("profile", "Institution selection dialog"),
    "CompanyDialog": ("profile", "Company selection dialog"),
    "LocalLLMTab": ("profile", "Local LLM model management (Tauri desktop)"),
    # --- Tenant & Organization ---
    "TenantSwitcher": (
        "tenant",
        "Switch between tenants/organizations with RBAC support",
    ),
    # --- Analytics ---
    "AnalyticsOverview": ("analytics", "Overview dashboard with key metrics"),
    "AnalyticsLayout": ("analytics", "Layout wrapper for analytics pages"),
    "AnalyticsUsersStats": ("analytics", "User activity statistics"),
    "AnalyticsTopicsStats": ("analytics", "Topic/conversation statistics"),
    "AnalyticsFinancialStats": ("analytics", "Financial/billing statistics"),
    "AnalyticsTranscriptsStats": ("analytics", "Transcript browsing and search"),
    "AnalyticsReports": ("analytics", "Report listing and management"),
    "AnalyticsReportDownload": ("analytics", "Download analytics reports"),
    "AnalyticsCourses": ("analytics", "Course analytics listing"),
    "AnalyticsCourseDetail": ("analytics", "Single course detail view"),
    "AnalyticsPrograms": ("analytics", "Program analytics listing"),
    "AnalyticsProgramDetail": ("analytics", "Single program detail view"),
    "StatCard": ("analytics", "Single statistic card"),
    "ChartCardWrapper": ("analytics", "Wrapper for chart visualizations"),
    "EmptyStats": ("analytics", "Empty state placeholder for stats"),
    "TimeFilter": ("analytics", "Time range filter dropdown"),
    "CustomDateRangePicker": ("analytics", "Custom date range selector"),
    "AccessTimeHeatmap": ("analytics", "Access time heatmap visualization"),
    "GroupsFilterDropdown": ("analytics", "Filter analytics by user groups"),
    "ChartFiltersProvider": (
        "analytics",
        "Context provider for chart filter state",
    ),
    "useChartFilters": ("analytics", "Hook for chart filter state"),
    "AnalyticsSettingsProvider": (
        "analytics",
        "Context provider for analytics settings",
    ),
    "useAnalyticsSettings": ("analytics", "Hook for analytics settings state"),
    "useOverview": ("analytics", "Hook to fetch overview metrics"),
    "useUsers": ("analytics", "Hook to fetch user statistics"),
    "useTopics": ("analytics", "Hook to fetch topic statistics"),
    "useFinancial": ("analytics", "Hook to fetch financial statistics"),
    "useTranscripts": ("analytics", "Hook to fetch transcript data"),
    "useReports": ("analytics", "Hook to fetch report data"),
    "useCourses": ("analytics", "Hook to fetch course analytics"),
    "usePrograms": ("analytics", "Hook to fetch program analytics"),
    # --- Notifications ---
    "NotificationDropdown": (
        "notifications",
        "Bell icon with unread badge -- compact navbar widget",
    ),
    "NotificationDisplay": (
        "notifications",
        "Full notification center with Inbox and Alerts tabs",
    ),
    "SendNotificationDialog": (
        "notifications",
        "Dialog to compose and send notifications (admin)",
    ),
    "AlertsTab": ("notifications", "Alert management tab"),
    "EditAlertDialog": ("notifications", "Dialog to create/edit alerts"),
    # --- Mentor UI (App Shell) ---
    "AppSidebar": (
        "mentor",
        "Collapsible sidebar with menu items, projects, pinned/recent messages",
    ),
    "NavBar": (
        "mentor",
        "Top navigation bar with user menu, mentor dropdown, new chat action",
    ),
    "ConversationStarters": (
        "mentor",
        "Guided prompt cards for starting conversations",
    ),
    # --- Workflows ---
    "WorkflowSidebar": ("workflows", "Workflow node type browser sidebar"),
    "ToolDialogs": ("workflows", "Tool configuration dialogs"),
    "ConnectorManagementDialog": (
        "workflows",
        "Connector setup and management",
    ),
    "CreateWorkflowModal": ("workflows", "Create new workflow modal"),
    "DeleteWorkflowModal": ("workflows", "Delete workflow confirmation"),
    # --- Content & Display ---
    "RichTextEditor": (
        "content",
        "Tiptap-based rich text editor (HTML or Markdown output)",
    ),
    "SearchableMultiSelect": (
        "content",
        "Multi-select dropdown with search filtering",
    ),
    "Markdown": (
        "content",
        "Markdown renderer with syntax highlighting and copy buttons",
    ),
    "AdvancedPagination": (
        "content",
        "Pagination with page numbers, prev/next, sibling pages",
    ),
    "TopBanner": ("content", "Dismissible top banner notification bar"),
    "Spinner": ("content", "Loading spinner (sm, md, lg)"),
    "Version": ("content", "App version display footer"),
    "TimeTrackingProvider": ("content", "Provider for automatic time tracking"),
    # --- Error Handling ---
    "ErrorPage": (
        "errors",
        "Error page with code, message, support link, home button",
    ),
    "ClientErrorPage": ("errors", "Client-side error boundary page"),
    # --- Hooks & Utilities ---
    "useLocalStorage": (
        "hooks",
        "Read/write localStorage with React state sync",
    ),
    "useIframeMessageHandler": (
        "hooks",
        "Handle postMessage events from iframes",
    ),
    "useTimeTracking": ("hooks", "Track user time spent on pages"),
    "useTimeTracker": ("hooks", "Time tracking hook (Next.js)"),
    "useTauri": ("hooks", "Tauri desktop app detection and bridge"),
    "useModelDownload": ("hooks", "Local LLM model download state (Tauri)"),
    "useGetChatDetails": ("hooks", "Fetch chat details hook (Next.js)"),
    "isTauriApp": ("hooks", "Check if running inside Tauri shell"),
    "sanitizeCss": ("hooks", "Sanitize user-provided CSS strings"),
    # --- Auto-discovered, now mapped ---
    "Loader": ("content", "Loading overlay component"),
    "CopyButtonIcon": ("content", "Copy-to-clipboard button icon"),
    "markdownComponents": ("content", "Custom renderers for Markdown component"),
    "TAURI_COMMANDS": ("hooks", "Tauri IPC command name constants"),
    "TAURI_EVENTS": ("hooks", "Tauri event name constants"),
    "initialModelDownloadState": ("hooks", "Initial state for model download"),
    "isLocalLLMEnabled": ("hooks", "Check if local LLM feature is enabled"),
    "setLocalLLMEnabled": ("hooks", "Enable/disable local LLM feature"),
    "AdvancedPagination": ("content", "Pagination with page numbers, prev/next, sibling pages"),
}

# Ordered category definitions: (key -> title)
CATEGORIES = [
    ("auth", "Authentication & SSO"),
    ("profile", "User Profile & Account"),
    ("tenant", "Tenant & Organization"),
    ("analytics", "Analytics"),
    ("notifications", "Notifications"),
    ("mentor", "Mentor UI (App Shell)"),
    ("workflows", "Workflows"),
    ("content", "Content & Display"),
    ("errors", "Error Handling"),
    ("hooks", "Hooks & Utilities"),
    ("types", "Types & Interfaces"),
    ("other", "Other"),
]

# UI primitives to list but not table-ify (too many, low signal).
UI_PRIMITIVE_NAMES = {
    "Button",
    "Input",
    "Badge",
    "Card",
    "CardHeader",
    "CardTitle",
    "CardDescription",
    "CardContent",
    "CardFooter",
    "AlertDialog",
    "Avatar",
    "Checkbox",
    "Dialog",
    "DropdownMenu",
    "Label",
    "Pagination",
    "Popover",
    "Progress",
    "RadioGroup",
    "Select",
    "Separator",
    "Sheet",
    "Sidebar",
    "Skeleton",
    "Switch",
    "Table",
    "Tabs",
    "Textarea",
    "Toast",
    "Toaster",
    "Toggle",
    "Tooltip",
    "Calendar",
    "Chart",
    "Sonner",
    "useToast",
}


# ---------------------------------------------------------------------------
# npm tarball fetching
# ---------------------------------------------------------------------------


def fetch_tarball_url() -> Tuple[str, str]:
    """Fetch the tarball URL and version from the npm registry."""
    resp = requests.get(NPM_REGISTRY_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["dist"]["tarball"], data["version"]


def download_tarball(url: str) -> bytes:
    """Download a tarball and return its bytes."""
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    chunks = []
    for chunk in resp.iter_content(chunk_size=8192):
        chunks.append(chunk)
    return b"".join(chunks)


def extract_dts_files(tarball_bytes: bytes) -> Dict[str, str]:
    """Extract .d.ts entry-point files from tarball bytes.

    Returns dict mapping subpath (".", "./next", "./sso") to file contents.
    """
    results: Dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tf:
        for subpath, member_path in ENTRY_POINTS.items():
            try:
                f = tf.extractfile(member_path)
                if f is not None:
                    results[subpath] = f.read().decode("utf-8")
            except (KeyError, AttributeError):
                pass
    return results


# ---------------------------------------------------------------------------
# .d.ts parsing
# ---------------------------------------------------------------------------

_RE_EXPORT_BLOCK = re.compile(r"export\s*\{([^}]+)\}", re.MULTILINE)
_RE_EXPORT_DECLARE = re.compile(
    r"export\s+declare\s+(function|const|let|var|class|enum)\s+(\w+)",
    re.MULTILINE,
)
_RE_EXPORT_TYPE = re.compile(
    r"export\s+(type|interface)\s+(\w+)", re.MULTILINE
)


def _classify_export(name: str, declare_kind: Optional[str] = None) -> str:
    """Classify an export by its name and/or declaration kind."""
    if declare_kind:
        kind_map = {
            "function": "function",
            "const": "const",
            "let": "const",
            "var": "const",
            "class": "component",
            "enum": "enum",
            "type": "type",
            "interface": "interface",
        }
        return kind_map.get(declare_kind, "unknown")
    if name[0:1].isupper():
        return "component"
    if name.startswith("use"):
        return "function"
    return "unknown"


def parse_exports(dts_content: str, subpath: str) -> List[ExportEntry]:
    """Parse all named exports from a .d.ts file."""
    import_path = IMPORT_PREFIX
    if subpath != ".":
        import_path = f"{IMPORT_PREFIX}/{subpath.lstrip('./')}"

    exports: Dict[str, ExportEntry] = {}

    # export { Foo, Bar, Baz }
    for match in _RE_EXPORT_BLOCK.finditer(dts_content):
        for item in match.group(1).split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split(" as ")
            name = parts[-1].strip()
            if name and name not in exports:
                exports[name] = ExportEntry(
                    name=name,
                    subpath=subpath,
                    import_path=import_path,
                    kind=_classify_export(name),
                )

    # export declare function/const/class/enum Name
    for match in _RE_EXPORT_DECLARE.finditer(dts_content):
        kind_str, name = match.group(1), match.group(2)
        if name not in exports:
            exports[name] = ExportEntry(
                name=name,
                subpath=subpath,
                import_path=import_path,
                kind=_classify_export(name, kind_str),
            )

    # export type/interface Name
    for match in _RE_EXPORT_TYPE.finditer(dts_content):
        kind_str, name = match.group(1), match.group(2)
        if name not in exports:
            exports[name] = ExportEntry(
                name=name,
                subpath=subpath,
                import_path=import_path,
                kind=_classify_export(name, kind_str),
            )

    return list(exports.values())


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


def is_react_component(entry: ExportEntry) -> bool:
    """Return True if the export is a React component (not a hook, const, type, etc.)."""
    # Explicit declaration kinds that are never components
    if entry.kind in ("function", "const", "type", "interface", "enum"):
        return False
    # Hooks (useXxx) are not visual components
    if entry.name.startswith("use"):
        return False
    # PascalCase with kind "component" or "unknown" — treat as component
    if entry.name[0:1].isupper() and entry.kind in ("component", "unknown"):
        return True
    return False


def categorize_exports(
    all_exports: List[ExportEntry],
    components_only: bool = False,
) -> Dict[str, CategoryDef]:
    """Group exports into ordered categories.

    Args:
        all_exports: All parsed exports.
        components_only: If True, only include React components (skip hooks,
            constants, types, utility functions).
    """
    cats: Dict[str, CategoryDef] = {}
    for key, title in CATEGORIES:
        cats[key] = CategoryDef(title=title)

    for entry in all_exports:
        # Skip UI primitives (listed separately)
        if entry.name in UI_PRIMITIVE_NAMES:
            continue

        # Filter to React components only when requested
        if components_only and not is_react_component(entry):
            continue

        if entry.name in COMPONENT_MAP:
            cat_key, _ = COMPONENT_MAP[entry.name]
        elif entry.kind in ("type", "interface"):
            cat_key = "types"
        elif entry.kind == "function" and entry.name.startswith("use"):
            cat_key = "hooks"
        else:
            cat_key = "other"

        if cat_key in cats:
            cats[cat_key].entries.append(entry)

    # Remove empty categories
    return {k: v for k, v in cats.items() if v.entries}


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------


def _get_description(entry: ExportEntry) -> str:
    """Get description for an export entry."""
    if entry.name in COMPONENT_MAP:
        _, desc = COMPONENT_MAP[entry.name]
        return desc
    return f"*(auto-discovered -- {entry.kind})*"


def _import_label(subpath: str) -> str:
    """Short label for the import column."""
    if subpath == ".":
        return "root"
    return subpath.lstrip("./")


def generate_gallery_markdown(
    categories: Dict[str, CategoryDef],
    version: str,
    ui_primitives: Optional[List[str]] = None,
    screenshots: Optional[Dict[str, str]] = None,
) -> str:
    """Generate the Component Gallery markdown section.

    Args:
        categories: Categorized exports to render.
        version: Package version string.
        ui_primitives: Optional list of UI primitive names.
        screenshots: Optional dict mapping category_key to image filename.
    """
    lines: List[str] = []
    lines.append("## Component Gallery")
    lines.append("")
    lines.append(
        f"All components below are from `@iblai/iblai-js/web-containers` "
        f"(v{version}). Use MCP tools"
    )
    lines.append(
        "(`get_component_info`, `get_hook_info`) for full props and usage examples."
    )
    lines.append("")
    lines.append(
        "> Auto-generated from `@iblai/web-containers@{v}` type declarations. "
        "Re-generate with: `iblai update-gallery <path>`".format(v=version)
    )
    lines.append("")

    for cat_key, cat in categories.items():
        lines.append(f"### {cat.title}")
        lines.append("")

        # Insert screenshot image if available
        if screenshots and cat_key in screenshots:
            img_file = screenshots[cat_key]
            lines.append(
                f"![{cat.title}]({GITHUB_RAW_BASE}/{img_file})"
            )
            lines.append("")

        lines.append("| Export | Import | Description |")
        lines.append("|--------|--------|-------------|")
        for entry in sorted(cat.entries, key=lambda e: e.name):
            desc = _get_description(entry)
            label = _import_label(entry.subpath)
            lines.append(f"| `{entry.name}` | {label} | {desc} |")
        lines.append("")

        # Import example: group by import_path
        by_path: Dict[str, List[str]] = {}
        for entry in sorted(cat.entries, key=lambda e: e.name):
            by_path.setdefault(entry.import_path, []).append(entry.name)

        lines.append("```typescript")
        for path, names in by_path.items():
            names_str = ", ".join(names[:6])
            if len(names) > 6:
                names_str += ", ..."
            lines.append(f'import {{ {names_str} }} from "{path}";')
        lines.append("```")
        lines.append("")

    # UI Primitives section
    if ui_primitives:
        lines.append("### UI Primitives (Shadcn/Radix)")
        lines.append("")
        lines.append(
            "These are bundled with the SDK and share the ibl.ai Tailwind theme. "
            "Available"
        )
        lines.append(
            "when you need lower-level building blocks inside SDK "
            "component customizations:"
        )
        lines.append("")
        lines.append(", ".join(f"`{n}`" for n in sorted(ui_primitives)))
        lines.append("")
        lines.append(
            "> **Note:** For your own UI, install shadcn/ui directly "
            "(`npx shadcn@latest add ...`)"
        )
        lines.append(
            "> rather than importing these from the SDK. The SDK exports "
            "are for internal use"
        )
        lines.append("> and SDK component customization.")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SKILL.md replacement
# ---------------------------------------------------------------------------


def replace_gallery_section(
    skill_content: str,
    gallery_markdown: str,
) -> str:
    """Replace the gallery section in a SKILL.md file."""
    start_idx = skill_content.find(START_MARKER)
    end_idx = skill_content.find(END_MARKER)

    if start_idx == -1:
        # No existing gallery -- append before end
        return skill_content.rstrip() + "\n\n" + gallery_markdown + "\n"

    if end_idx == -1:
        # Start marker but no end marker -- replace to end
        return skill_content[:start_idx] + gallery_markdown + "\n"

    # Both markers -- replace between them
    return (
        skill_content[:start_idx] + gallery_markdown + "\n" + skill_content[end_idx:]
    )


# ---------------------------------------------------------------------------
# Screenshot pipeline
# ---------------------------------------------------------------------------

# Demo pages to create for categories that don't have generated pages.
_DEMO_PAGES: Dict[str, Tuple[str, str]] = {
    # path relative to app dir -> (route used by Playwright, file content)
    "app/(app)/profile/page.tsx": (
        "/profile",
        '''"use client";
import { useEffect, useState } from "react";
import { UserProfileModal } from "@iblai/iblai-js/web-containers/next";
import config from "@/lib/iblai/config";
import { resolveAppTenant } from "@/lib/iblai/tenant";

export default function ProfilePage() {
  const [tenant, setTenant] = useState("");
  useEffect(() => { setTenant(resolveAppTenant()); }, []);
  if (!tenant) return null;
  return (
    <div className="min-h-screen bg-background p-8">
      <UserProfileModal
        isOpen={true}
        tenantKey={tenant}
        authURL={config.authUrl}
        onClose={() => {}}
      />
    </div>
  );
}
''',
    ),
    "app/(app)/notifications/page.tsx": (
        "/notifications",
        '''"use client";
import { useEffect, useState } from "react";
import { NotificationDisplay } from "@iblai/iblai-js/web-containers";
import { resolveAppTenant } from "@/lib/iblai/tenant";

export default function NotificationsPage() {
  const [tenant, setTenant] = useState("");
  const [userId, setUserId] = useState("");
  useEffect(() => {
    setTenant(resolveAppTenant());
    try {
      const ud = JSON.parse(localStorage.getItem("userData") || "{}");
      setUserId(ud.user_id || ud.username || "");
    } catch {}
  }, []);
  if (!tenant || !userId) return null;
  return (
    <div className="min-h-screen bg-background p-8">
      <NotificationDisplay org={tenant} userId={userId} />
    </div>
  );
}
''',
    ),
    "app/(app)/error-demo/page.tsx": (
        "/error-demo",
        '''"use client";
import { ErrorPage } from "@iblai/iblai-js/web-containers/next";

export default function ErrorDemoPage() {
  return (
    <ErrorPage
      errorCode={404}
      errorMessage="This page could not be found."
      homeUrl="/"
    />
  );
}
''',
    ),
}


def _scaffold_temp_app(
    tmpdir: str,
    platform: str,
) -> Path:
    """Scaffold a temp Next.js app with all features enabled."""
    app_name = "gallery-screenshots"
    app_dir = Path(tmpdir) / app_name

    # iblai startapp agent --yes
    subprocess.run(
        [
            sys.executable,
            "-m",
            "iblai.cli",
            "--no-update",
            "startapp",
            "agent",
            "--yes",
            "--platform",
            platform,
            "--app-name",
            app_name,
        ],
        cwd=tmpdir,
        check=True,
        capture_output=True,
        text=True,
    )

    # Add features
    for feature in ["profile", "account", "analytics", "notifications"]:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "iblai.cli",
                "--no-update",
                "add",
                feature,
            ],
            cwd=str(app_dir),
            check=True,
            capture_output=True,
            text=True,
        )

    return app_dir


def _create_demo_pages(app_dir: Path) -> None:
    """Write demo pages for categories not covered by generators."""
    for rel_path, (_route, content) in _DEMO_PAGES.items():
        page_path = app_dir / rel_path
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(content, encoding="utf-8")


def _install_and_start(app_dir: Path) -> subprocess.Popen:
    """Install deps, Playwright, and start the dev server.

    Returns the dev server Popen handle.
    """
    # Install dependencies
    subprocess.run(
        ["pnpm", "install"],
        cwd=str(app_dir),
        check=True,
        capture_output=True,
        text=True,
    )

    # Install Playwright chromium
    subprocess.run(
        ["npx", "playwright", "install", "chromium"],
        cwd=str(app_dir),
        check=True,
        capture_output=True,
        text=True,
    )

    # Start dev server in background
    server = subprocess.Popen(
        ["pnpm", "dev"],
        cwd=str(app_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    # Wait for server to be ready (poll localhost:3000)
    import urllib.request
    import urllib.error

    for _ in range(60):
        time.sleep(2)
        try:
            urllib.request.urlopen("http://localhost:3000", timeout=2)
            break
        except (urllib.error.URLError, OSError):
            if server.poll() is not None:
                raise RuntimeError(
                    f"Dev server exited with code {server.returncode}"
                )
    else:
        _cleanup(server)
        raise RuntimeError("Dev server did not start within 120 seconds")

    return server


def _authenticate(
    app_dir: Path,
    username: str,
    password: str,
) -> Path:
    """Authenticate via Playwright and save storage state.

    Returns path to the storage state JSON file.
    """
    storage_path = app_dir / "playwright-storage.json"

    script = f"""
const {{ chromium }} = require('playwright');

(async () => {{
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Navigate to app — should redirect to login
  await page.goto('http://localhost:3000');
  await page.waitForURL(/login|auth/, {{ timeout: 15000 }});

  // Fill credentials and submit
  await page.fill('input[name="username"], input[type="email"], #username', '{username}');
  await page.fill('input[name="password"], input[type="password"], #password', '{password}');
  await page.click('button[type="submit"], input[type="submit"]');

  // Wait for redirect back to app
  await page.waitForURL('http://localhost:3000/**', {{ timeout: 30000 }});
  await page.waitForLoadState('networkidle');

  // Save storage state (cookies + localStorage)
  await context.storageState({{ path: '{storage_path}' }});

  await browser.close();
}})();
"""
    script_path = app_dir / "_auth.js"
    script_path.write_text(script, encoding="utf-8")

    subprocess.run(
        ["node", str(script_path)],
        cwd=str(app_dir),
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    return storage_path


def _take_screenshot(
    storage_state: Path,
    route: str,
    output_path: Path,
) -> None:
    """Take a screenshot of a single route using Playwright."""
    if route == "__login__":
        # Screenshot the login page (unauthenticated)
        script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000');
  await page.waitForURL(/login|auth/, {{ timeout: 15000 }});
  await page.waitForLoadState('networkidle');
  await page.screenshot({{ path: '{output_path}', fullPage: true }});
  await browser.close();
}})();
"""
    else:
        script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const browser = await chromium.launch();
  const context = await browser.newContext({{
    storageState: '{storage_state}'
  }});
  const page = await context.newPage();
  await page.goto('http://localhost:3000{route}');
  await page.waitForLoadState('networkidle');
  // Extra wait for dynamic components to render
  await page.waitForTimeout(3000);
  await page.screenshot({{ path: '{output_path}', fullPage: true }});
  await browser.close();
}})();
"""
    script_path = storage_state.parent / f"_screenshot_{output_path.stem}.js"
    script_path.write_text(script, encoding="utf-8")

    subprocess.run(
        ["node", str(script_path)],
        cwd=str(storage_state.parent),
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _cleanup(server: subprocess.Popen) -> None:
    """Kill the dev server process group."""
    try:
        os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        server.wait(timeout=10)
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


def generate_screenshots(
    skill_dir: Path,
    platform: str,
    username: str,
    password: str,
) -> Dict[str, str]:
    """Full screenshot pipeline.

    Returns dict mapping category_key to image filename.
    """
    tmpdir = tempfile.mkdtemp(prefix="iblai-gallery-")
    server = None
    try:
        # 1. Scaffold temp app
        app_dir = _scaffold_temp_app(tmpdir, platform)

        # 2. Create demo pages
        _create_demo_pages(app_dir)

        # 3. Install and start dev server
        server = _install_and_start(app_dir)

        # 4. Authenticate
        storage_state = _authenticate(app_dir, username, password)

        # 5. Take screenshots
        screenshots: Dict[str, str] = {}
        for cat_key, route, filename in SCREENSHOT_PAGES:
            output_path = skill_dir / filename
            try:
                _take_screenshot(storage_state, route, output_path)
                screenshots[cat_key] = filename
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Skip failed screenshots — don't block the whole run
                pass

        return screenshots
    finally:
        if server:
            _cleanup(server)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# High-level orchestrator
# ---------------------------------------------------------------------------


# The SKILL.md lives at <skills_dir>/iblai-components/SKILL.md.
SKILL_RELATIVE_PATH = "iblai-components/SKILL.md"


def resolve_skill_path(skills_dir: str) -> Path:
    """Resolve the SKILL.md path from a skills directory.

    Accepts either:
      - A directory containing ``iblai-components/SKILL.md``
      - A direct path to a SKILL.md file (backwards-compatible)
    """
    p = Path(skills_dir)
    if p.is_file():
        return p
    candidate = p / SKILL_RELATIVE_PATH
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(
        f"Cannot find SKILL.md at {candidate} "
        f"(looked in {p.resolve()})"
    )


def update_gallery(
    skills_dir: str,
    screenshots: Optional[Dict[str, str]] = None,
) -> Tuple[str, str, int, str]:
    """Full pipeline: fetch, parse, generate, replace.

    Args:
        skills_dir: Path to the skills directory (or a SKILL.md file for
            backwards compatibility).
        screenshots: Optional dict mapping category_key to image filename,
            as returned by ``generate_screenshots()``.

    Returns (version, updated_content, export_count, resolved_skill_path).
    """
    skill_path = resolve_skill_path(skills_dir)

    # 1. Fetch tarball info
    tarball_url, version = fetch_tarball_url()

    # 2. Download tarball
    tarball_bytes = download_tarball(tarball_url)

    # 3. Extract .d.ts files
    dts_files = extract_dts_files(tarball_bytes)

    # 4. Parse exports from all entry points
    all_exports: List[ExportEntry] = []
    for subpath, content in dts_files.items():
        all_exports.extend(parse_exports(content, subpath))

    # 5. UI primitives are not individually named in .d.ts barrel exports
    #    but are available in the package. Include the static list.
    ui_primitives = sorted(UI_PRIMITIVE_NAMES - {"useToast"})

    # 6. Categorize (React components only)
    categories = categorize_exports(all_exports, components_only=True)

    # 7. Generate markdown
    gallery_md = generate_gallery_markdown(
        categories, version, ui_primitives, screenshots
    )

    # 8. Read current file and replace section
    current_content = skill_path.read_text(encoding="utf-8")
    updated = replace_gallery_section(current_content, gallery_md)

    total_exports = sum(len(c.entries) for c in categories.values())
    total_exports += len(ui_primitives)
    return version, updated, total_exports, str(skill_path)
