<div align="center">

<a href="https://ibl.ai"><img src="https://ibl.ai/images/iblai-logo.png" alt="ibl.ai" width="300"></a>

# App CLI

Interactive CLI for building apps on the [ibl.ai](https://ibl.ai) platform. Scaffold full applications from scratch, add ibl.ai components to existing Next.js projects, or build for desktop and mobile with Tauri v2.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![npm](https://img.shields.io/npm/v/@iblai/cli?label=npm%20%40iblai%2Fcli)](https://www.npmjs.com/package/@iblai/cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Prerequisites

- **Node.js 18+** and a package manager (**pnpm** recommended, npm or yarn also work)
- **Python 3.11+** (only required for the `pip` or source install methods)
- **An ibl.ai platform account** -- register for free at [iblai.app](https://iblai.app) to get a tenant key and configure agents
- **Rust toolchain** (only required for Tauri desktop/mobile builds)

## Install

### npm (recommended)

```bash
npx @iblai/cli --help
```

Or install globally:

```bash
npm install -g @iblai/cli
```

### pip

```bash
pip install iblai-app-cli
```

### Source

```bash
git clone https://github.com/iblai/iblai-app-cli.git
cd iblai-app-cli
make -C .iblai install
```

Verify the installation:

```bash
iblai --version
```

## Quick Start

### 1. Build a Full App from Scratch

Scaffold a complete AI agent chat application with SSO authentication, sidebar, navbar, and WebSocket chat:

```bash
iblai startapp agent
```

The interactive wizard prompts for your platform key, agent ID, and app name. Then:

```bash
cd my-agent-app
pnpm install
cp .env.example .env.local    # Edit with your platform credentials
pnpm dev                       # Opens on http://localhost:3000
```

For a minimal app with authentication only (no chat UI, no sidebar):

```bash
iblai startapp base
```

### 2. Add Auth to Your Existing App

Already have a Next.js project? Add ibl.ai SSO authentication without scaffolding a new app:

```bash
cd your-existing-nextjs-app
iblai add auth --platform your-tenant
```

This generates 7 files -- SSO callback page, Redux store, auth utilities, providers, and SDK styles -- all namespaced under `lib/iblai/` and `components/iblai/` to avoid conflicts with your existing code. Follow the printed instructions to wire up providers and install dependencies.

### 3. Add an AI Chat Widget

Drop in a full-featured AI chat widget powered by the `<mentor-ai>` web component:

```bash
iblai add chat
```

Then use it anywhere in your app:

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";

<ChatWidget mentorId="your-agent-id" />
```

The widget includes WebSocket streaming, markdown rendering, session persistence, file attachments, and conversation starters.

### 4. Build for Mobile and Desktop

Add Tauri v2 support for native desktop and mobile builds:

```bash
iblai add builds
```

Then use the `iblai builds` commands:

```bash
iblai builds dev                       # Dev mode (Next.js + native shell)
iblai builds build                     # Production build for current platform
iblai builds generate-icons logo.png   # Generate all icon sizes
iblai builds ci-workflow --all         # Generate CI build workflows
```

iOS and Windows are also supported:

```bash
iblai builds ios init          # Initialize iOS project (macOS only)
pnpm tauri:dev:ios             # Run in iOS Simulator
pnpm tauri:build:msix          # Build Windows MSIX package
```

### 5. Mix and Match Components

Cherry-pick exactly the features you need. Each component can be added independently (auth is required before the others):

```bash
iblai add auth            # Start here -- required by other components
iblai add chat            # AI chat widget
iblai add profile         # User profile dropdown
iblai add notifications   # Notification bell with unread badge
iblai add analytics       # Analytics dashboard
iblai add account         # Organization/account settings
iblai add mcp             # MCP server config + AI assistant skills
iblai add builds          # Tauri v2 desktop/mobile shell
```

## Component Catalog

| Component | Command | What It Does |
|-----------|---------|-------------|
| **auth** | `iblai add auth` | SSO authentication -- redirects to ibl.ai login, returns with session. Generates Redux store, providers, and auth utilities. |
| **chat** | `iblai add chat` | AI chat widget using the `<mentor-ai>` web component. WebSocket streaming, markdown, file attachments, session persistence. |
| **profile** | `iblai add profile` | User profile dropdown with avatar, profile link, and logout action. |
| **account** | `iblai add account` | Organization and account settings page. |
| **analytics** | `iblai add analytics` | Analytics dashboard for viewing platform metrics. |
| **notifications** | `iblai add notifications` | Real-time notification bell with unread count badge. |
| **builds** | `iblai add builds` | Tauri v2 desktop/mobile shell with icon generation and CI workflow scaffolding. |
| **mcp** | `iblai add mcp` | MCP server configuration plus Claude Code, OpenCode, and Cursor skill files. |

## shadcn/ui Integration

When ibl.ai does not have a pre-built component for your use case, use [shadcn/ui](https://ui.shadcn.com) as a fallback. Generated apps include a `components.json` that configures the shadcn CLI out of the box:

```bash
npx shadcn@latest add button dialog table form
npx shadcn@latest add @shadcn-space/hero-01
npx shadcn@latest add @shadcn-space/pricing-01
```

shadcn/ui components and ibl.ai SDK components share the same Tailwind CSS theme configuration, so they look visually identical without additional styling work. The brand colors, spacing, border radius, and typography are all driven by the same design tokens defined in `tailwind.config.ts` and the ibl.ai CSS variables.

Browse available blocks at [shadcnspace.com/blocks](https://shadcnspace.com/blocks).

## AI-Assisted Development

### MCP Server

The `@iblai/mcp` server provides tools for AI assistants to query SDK internals without searching the codebase:

```
get_component_info("Profile")                  # Full props interface for any SDK component
get_hook_info("useAdvancedChat")               # Hook parameters and return types
get_api_query_info("useGetUserMetadataQuery")  # RTK Query endpoint details
get_provider_setup("auth")                     # Provider hierarchy and setup code
create_page_template("Dashboard", "mentor")    # Generate a page template
```

Add MCP support to your project:

```bash
iblai add mcp
```

This generates `.mcp.json` and skill files for Claude Code, OpenCode, and Cursor.

### Skills

13 AI assistant skills are available in the [`skills/`](skills/) directory. Invoke them with `/` in Claude Code, OpenCode, or Cursor:

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
| `/iblai-add-shadcn-component` | Add shadcnspace blocks with ibl.ai brand consistency |
| `/iblai-add-test` | Playwright E2E test patterns |
| `/iblai-build-windows-msix` | Windows MSIX build for test and release |
| `/iblai-generate-icons` | Generate all Tauri icon sizes from a source image |

### AI-Customized Scaffolding

Use the `--prompt` flag when scaffolding to customize styling, copy, and layout via an LLM:

```bash
iblai startapp agent --platform acme \
  --anthropic-key sk-ant-... \
  --prompt "Make this a kids learning assistant with bright colors"
```

Or with OpenAI:

```bash
iblai startapp agent --platform acme \
  --openai-key sk-... \
  --prompt "Make this a developer tools assistant with a dark theme"
```

The AI modifies text, colors, and styling but never changes imports, component interfaces, or hook calls.

## Deployment

### Vercel

Generated apps are standard Next.js 16 projects and deploy to [Vercel](https://vercel.com) with zero configuration. Set the environment variables in your Vercel project settings.

### Docker

Generated apps support Docker deployment with runtime environment injection via `public/env.js`:

```bash
docker build -t my-iblai-app .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.iblai.app \
  -e NEXT_PUBLIC_AUTH_URL=https://login.iblai.app \
  my-iblai-app
```

### App Store Builds (Tauri)

For desktop and mobile distribution, add the Tauri build shell and use the CI workflows:

```bash
iblai add builds
iblai builds build                     # Build for current platform
iblai builds ci-workflow --all         # Generate GitHub Actions for all platforms
```

Supported targets include macOS (.dmg), Windows (.msix), Linux (.deb/.AppImage), iOS (.ipa), and Android (.apk).

## Environment Configuration

Apps connect to [iblai.app](https://iblai.app) by default. Copy `.env.example` to `.env.local` and customize:

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.app
NEXT_PUBLIC_AUTH_URL=https://login.iblai.app
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.app
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.app
NEXT_PUBLIC_MAIN_TENANT_KEY=iblai
```

| Variable | Description |
|----------|-------------|
| **`NEXT_PUBLIC_API_BASE_URL`** | Base URL for the ibl.ai REST API |
| **`NEXT_PUBLIC_AUTH_URL`** | SSO login page URL |
| **`NEXT_PUBLIC_BASE_WS_URL`** | WebSocket URL for real-time chat streaming |
| **`NEXT_PUBLIC_PLATFORM_BASE_DOMAIN`** | Platform domain (used for cookie scoping and URL construction) |
| **`NEXT_PUBLIC_MAIN_TENANT_KEY`** | Your organization's tenant key on the ibl.ai platform |

## Example App

See [`examples/iblai-agent-app/`](examples/iblai-agent-app/) for a complete reference application featuring:

- **SSO authentication** with route group isolation
- **AI agent chat** with the `<mentor-ai>` web component
- **Tauri v2 desktop support** for macOS, Windows, and Linux
- **Playwright E2E tests** for authentication and chat flows

## Development

For CLI contributors -- the Python package, generators, templates, and tests live under `.iblai/`:

```bash
make -C .iblai install-dev    # Install with dev dependencies (tests, linting)
make -C .iblai test           # Run the test suite (255+ tests)
make -C .iblai lint           # Check code formatting (black + flake8)
make -C .iblai format         # Auto-format code with black
make -C .iblai binary         # Build standalone binary for current platform
make -C .iblai example        # Regenerate the example app
make -C .iblai help           # Show all available targets
```

### Key Technologies

| Category | Technology |
|----------|-----------|
| **Framework** | Next.js 16 (App Router) |
| **UI** | React 19, Tailwind CSS 4, shadcn/ui (Radix UI) |
| **State** | Redux Toolkit + React-Redux |
| **SDK** | `@iblai/iblai-js` (auth, chat, data layer, web components) |
| **Desktop/Mobile** | Tauri v2 |
| **Language** | TypeScript |

See the [development guide](.iblai/README.md) for project structure, test patterns, and contribution workflow.

## License

MIT -- [ibl.ai](https://ibl.ai)
