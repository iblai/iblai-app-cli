# CLAUDE.md

> **For app developers.** For CLI development, see [.iblai/CLAUDE.md](.iblai/CLAUDE.md).

This file provides guidance for working with the example app and generated ibl.ai applications.

## MCP Server (Use First)

`.mcp.json` is configured with `@iblai/mcp`. **Always use MCP tools first** before searching the codebase:

```
get_component_info("Profile")                  # Full props interface for any SDK component
get_hook_info("useAdvancedChat")               # Hook parameters and return types
get_api_query_info("useGetUserMetadataQuery")  # RTK Query endpoint details
get_provider_setup("auth")                     # Provider hierarchy and setup code
create_page_template("Dashboard", "mentor")    # Generate a page template
```

## Project Overview

**ibl.ai App CLI** — scaffolds Next.js 15 apps with ibl.ai SSO authentication, Redux Toolkit store, Tauri v2 desktop/mobile shell, and pre-built SDK components.

The example app at `examples/iblai-agent-app/` is a complete reference implementation with the agent template (full-screen ChatWidget via `<mentor-ai>` web component).

## Brand Identity

See [BRAND.md](BRAND.md) for the complete ibl.ai brand guidelines: color palette, gradients, typography, spacing, and CSS utility classes.

Key values for quick reference:
- **Primary**: `#0058cc` (brand blue)
- **Gradient**: `linear-gradient(135deg, #00b0ef, #0058cc)`
- **Button**: `from-[#2563EB] to-[#93C5FD]`

## Commands (Generated Apps)

```bash
# Development
pnpm dev                # Start dev server (localhost:3000)
pnpm build              # Production build
pnpm lint               # ESLint
pnpm typecheck          # TypeScript type checking

# E2E tests
pnpm test:e2e           # Headless (Chromium + Firefox + WebKit)
pnpm test:e2e:ui        # Interactive Playwright UI

# Tauri desktop/mobile
iblai builds dev                     # Dev mode (Next.js + native shell)
iblai builds build                   # Production build for current platform
iblai builds generate-icons logo.png # Generate all icon sizes
iblai builds ci-workflow --all       # Generate CI build workflows

# iOS
iblai builds ios init                # Initialize iOS project (macOS only)
pnpm tauri:dev:ios                   # Run in iOS Simulator
pnpm tauri:build:ios                 # Build iOS app (.ipa)

# Windows MSIX
pnpm tauri:build:msix                # Build MSIX package (x64)
pnpm tauri:setup:cert                # Create dev certificate for signing
```

## Architecture (Generated Apps)

### Route Groups

```
app/
├── (auth)/sso-login-complete/   # SSO callback — runs OUTSIDE providers
└── (app)/                       # Authenticated routes — wrapped by AppShell
    ├── layout.tsx               # AppShell + providers
    └── page.tsx                 # Home page
```

### Providers (`providers/index.tsx`)

```
AuthProvider > TenantProvider > {children}
```

`initializeDataLayer` is called synchronously with **5 arguments** (data-layer v1.2+):

```typescript
initializeDataLayer(dmUrl, lmsUrl, legacyLmsUrl, storageService, httpErrorHandler)
```

### Redux Store (`store/index.ts`)

`@reduxjs/toolkit` is deduplicated via webpack `resolve.alias` in `next.config.mjs`. Without deduplication, SDK components use a different `ReactReduxContext` and RTK Query hooks silently return `undefined`.

### Pre-built Components (`components/iblai/`)

| Component | Description |
|-----------|-------------|
| `ChatWidget` | `<mentor-ai>` web component — full-screen AI chat |
| `ProfileDropdown` | Avatar dropdown with profile link and logout |
| `IblaiNotificationBell` | Bell icon with unread count badge |

## SDK Versions (Locked)

| Package | Version |
|---------|---------|
| `@iblai/iblai-js` | 1.1.1 |
| `@iblai/iblai-web-mentor` | 2.0.1 |
| `@iblai/iblai-api` | 4.166.0-ai |
| `@reduxjs/toolkit` | 2.11.2 |
| `next` | 15.5.14 |

## Add Features

```bash
iblai add auth           # SSO authentication + Redux store + providers
iblai add chat           # AI chat widget (<mentor-ai> web component)
iblai add profile        # User profile dropdown
iblai add notifications  # Notification bell with unread badge
iblai add mcp            # MCP server config + Claude/OpenCode/Cursor skills
iblai add builds         # Tauri v2 desktop/mobile shell
```

## Environment (`.env.local`)

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.app
NEXT_PUBLIC_AUTH_URL=https://login.iblai.app
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.app
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.app
NEXT_PUBLIC_MAIN_TENANT_KEY=your-tenant
NEXT_PUBLIC_DEFAULT_AGENT_ID=your-mentor-id
```

## Skills

Available in `skills/` (invoke with `/` in Claude Code, OpenCode, or Cursor):

### App Skills (13)

| Skill | Description |
|-------|-------------|
| `/iblai-setup` | What's set up, env config, localStorage keys, MCP tools |
| `/iblai-add-auth` | Add SSO authentication |
| `/iblai-add-chat` | AI chat widget + customization |
| `/iblai-add-profile` | Profile dropdown + full settings page |
| `/iblai-add-account` | Organization/account settings |
| `/iblai-add-analytics` | Analytics dashboard |
| `/iblai-add-notifications` | Notification bell + center page |
| `/iblai-add-component` | Generic guide for any SDK component |
| `/iblai-add-shadcn-component` | Add shadcnspace blocks with brand consistency |
| `/iblai-add-test` | Playwright E2E test patterns |
| `/iblai-build-windows-msix` | Windows MSIX build for test and release |
| `/iblai-generate-icons` | Generate all icon sizes from a source image |

### CLI Dev Skills (6)

| Skill | Description |
|-------|-------------|
| `/iblai-cli-startapp` | How `iblai startapp` and the generator hierarchy work |
| `/iblai-cli-add-command` | How `iblai add` integrates features into existing projects |
| `/iblai-cli-builds` | How `iblai builds` wraps @tauri-apps/cli |
| `/iblai-cli-build-binary` | Building standalone binaries with PyInstaller |
| `/iblai-cli-publish` | Release workflow: GitHub releases, npm, PyPI |
| `/iblai-cli-templates` | Jinja2 template system: directories, context, conditionals |

## CLI Development

For CLI development (Python package, generators, templates, tests), see [.iblai/CLAUDE.md](.iblai/CLAUDE.md).

Quick reference:

```bash
make -C .iblai install-dev    # Install with dev dependencies
make -C .iblai test           # Run 255+ tests
make -C .iblai example        # Regenerate example app
make -C .iblai help           # Show all targets
```

THIS PROJECT ALREADY HAS GIT INITIALIZED. DO NOT INITIALIZE GIT.
