<div align="center">

<a href="https://ibl.ai"><img src="https://ibl.ai/images/iblai-logo.png" alt="ibl.ai" width="300"></a>

# App CLI

Interactive CLI for scaffolding [ibl.ai](https://ibl.ai) frontend applications, or adding ibl.ai features (auth, chat, profile, notifications) to existing Next.js apps. Generates production-ready code with SSO authentication, WebSocket chat, and full integration with the ibl.ai platform SDK.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Prerequisites

- **Python 3.8+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **[Node.js 18+](https://nodejs.org/)** and **[pnpm](https://pnpm.io/)** for running generated apps
- **An ibl.ai platform account** with a platform and at least one agent configured

### Dependencies installed automatically

The following are installed as Python package dependencies:

- **click** (>= 8.0) -- CLI framework
- **jinja2** (>= 3.0) -- template rendering engine
- **rich** (>= 13.0) -- terminal formatting and UI
- **inquirer** (>= 3.0) -- interactive prompts
- **anthropic** (>= 0.40) -- AI-assisted generation (optional)
- **openai** (>= 1.0) -- AI-assisted generation (optional)

## Install

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo
git clone git@github.com:iblai/iblai-app-cli.git
cd iblai-app-cli

# Create a virtual environment and install
uv venv
source .venv/bin/activate
uv pip install .
```

For development:

```bash
uv pip install -e ".[dev]"
```

Using pip:

```bash
pip install .
```

### Verify installation

```bash
iblai --version
```

## Usage

Run `iblai --help` to see all available commands.

```
Usage: iblai [OPTIONS] COMMAND [ARGS]...

  ibl.ai CLI - Quickly scaffold ibl.ai applications.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  startapp  Create a new ibl.ai application from a template.
```

### Templates

| Template | Description | Command |
|----------|-------------|---------|
| `base` | Minimal app with ibl.ai auth — blank canvas for custom development | `iblai startapp base` |
| `agent` | Full AI agent chat application with sidebar, navbar, WebSocket chat | `iblai startapp agent` |

### `iblai startapp base`

Scaffolds a minimal Next.js 16 app with ibl.ai SSO authentication, Redux store, and providers — no chat UI, no sidebar, no agent routes. A blank canvas for building your own app with `iblai add` features or custom code.

```bash
iblai startapp base --platform acme
```

What you get (~22 files):
- SSO authentication with route group isolation (`(auth)/sso-login-complete`)
- Redux store with `coreApiSlice` (no chat/mentor slices)
- `AuthProvider` + `TenantProvider` (no `MentorProvider`)
- Consolidated API URL config (`api.basedomain/lms`, `/dm`, `/axd`)
- Home page with user greeting, logout, and hints for `iblai add`
- `components.json` for shadcnspace UI blocks
- `.mcp.json` for AI-assisted development
- Pinned dependency versions matching the ibl.ai SDK

Add features later:
```bash
iblai add chat           # AI chat widget
iblai add profile        # User profile dropdown
iblai add notification  # Notification bell
iblai add mcp            # Claude skills
```

### `iblai startapp agent`

Scaffolds a complete Next.js 16 agent chat application with SSO authentication, Redux state management, and full ibl.ai SDK integration.

```bash
iblai startapp agent --platform acme --agent my-bot-123
```

Interactive wizard that walks you through:

1. **Platform key** -- your ibl.ai platform identifier
2. **Agent ID** -- the agent/mentor to connect to (optional, can be set later)
3. **App name** -- directory name for the generated project

#### Options

```
Options:
  --platform, -p TEXT         Platform key
  --agent, -a TEXT            Agent ID
  --app-name TEXT             App name (used for directory and package.json)
  --output, -o PATH           Output directory (default: current directory)
  --openai-key TEXT           OpenAI API key for AI-assisted customization
  --anthropic-key TEXT        Anthropic API key for AI-assisted customization
  --ai-provider TEXT          AI provider: "openai" or "anthropic"
  --ai-model TEXT             AI model override (e.g., claude-sonnet-4-20250514)
  --ai-temperature FLOAT      AI temperature (0.0-2.0)
  --ai-max-tokens INTEGER     AI max tokens for generation
  --prompt, -P TEXT           Natural language prompt to customize the app
  --env-file PATH             Path to a custom .env file
  --stage TEXT                Stage name to load .env.{stage} overrides
  --help                      Show this message and exit
```

#### Configuration via `.env` files

Instead of passing all options as CLI flags, you can create a `.env` file:

```bash
# .env
IBLAI_PLATFORM_KEY=acme
IBLAI_AGENT_ID=my-agent-123
IBLAI_APP_NAME=my-custom-app
OPENAI_API_KEY=sk-...
IBLAI_AI_PROVIDER=openai
IBLAI_AI_MODEL=gpt-4-turbo-preview
IBLAI_AI_TEMPERATURE=0.5
IBLAI_PROMPT="Make this a kids learning assistant"
```

Stage-specific overrides are supported via `.env.{stage}` files:

```bash
# .env.production
IBLAI_PLATFORM_KEY=acme-prod
IBLAI_AGENT_ID=production-agent-456
```
```bash
iblai startapp agent --stage production
```

Configuration priority (highest wins):

```
CLI flags > System env vars > .env.{DEV_STAGE} > .env > interactive prompts
```

#### Environment variables

| Variable | CLI Flag | Description |
|----------|----------|-------------|
| `IBLAI_PLATFORM_KEY` | `--platform` | Platform key |
| `IBLAI_AGENT_ID` | `--agent` | Agent / mentor ID |
| `IBLAI_APP_NAME` | `--app-name` | App name for directory and package.json |
| `IBLAI_OUTPUT_DIR` | `--output` | Output directory |
| `OPENAI_API_KEY` | `--openai-key` | OpenAI API key |
| `ANTHROPIC_API_KEY` | `--anthropic-key` | Anthropic API key |
| `IBLAI_AI_PROVIDER` | `--ai-provider` | AI provider (`openai` or `anthropic`) |
| `IBLAI_AI_MODEL` | `--ai-model` | AI model override |
| `IBLAI_AI_TEMPERATURE` | `--ai-temperature` | AI temperature |
| `IBLAI_AI_MAX_TOKENS` | `--ai-max-tokens` | AI max tokens |
| `IBLAI_PROMPT` | `--prompt` | Enhancement prompt |
| `DEV_STAGE` | `--stage` | Stage name for `.env.{stage}` |

#### Examples

```bash
# Interactive mode (prompts for all required values)
iblai startapp agent

# Non-interactive with platform and agent
iblai startapp agent --platform acme --agent my-agent-123

# Fully non-interactive
iblai startapp agent --platform acme --agent my-agent-123 --app-name my-app

# Generate into a specific directory
iblai startapp agent --platform acme --output ./projects

# AI-assisted customization (modifies styling, copy, and layout)
iblai startapp agent --platform acme \
  --anthropic-key sk-ant-... \
  --prompt "Make this a kids learning assistant with bright colors"

# With AI model and temperature overrides
iblai startapp agent --platform acme \
  --anthropic-key sk-ant-... \
  --ai-model claude-sonnet-4-20250514 \
  --ai-temperature 0.5 \
  --prompt "Make this a developer tools assistant"

# Using a custom .env file
iblai startapp agent --env-file ./config/.env

# Using stage-specific config
iblai startapp agent --stage production
```

### Running the generated app

After generation, the CLI prints next steps:

```bash
cd <app-name>
pnpm install
cp .env.example .env.local    # Edit with your platform URL and keys
pnpm dev                       # Starts on http://localhost:3000
```

## Add UI blocks (shadcnspace)

Generated apps include a `components.json` that enables the [shadcn/ui CLI](https://ui.shadcn.com/docs/cli). You can add production-ready UI blocks from [shadcnspace](https://shadcnspace.com) with a single command:

```bash
npx shadcn@latest add @shadcn-space/hero-01
npx shadcn@latest add @shadcn-space/pricing-01
npx shadcn@latest add @shadcn-space/dashboard-shell-01
```

Browse all available blocks at [shadcnspace.com/blocks](https://shadcnspace.com/blocks).

## `iblai add` -- Add ibl.ai Features to Existing Apps

Already have a Next.js app? Use `iblai add` to integrate ibl.ai features without scaffolding a new project.

```bash
iblai add auth           # SSO authentication + Redux store + providers
iblai add chat           # AI chat widget with WebSocket streaming
iblai add profile        # User profile dropdown
iblai add notification  # Notification bell with unread badge
iblai add mcp            # MCP config + Claude skills for AI-assisted development
```

### `iblai add auth`

Adds SSO authentication to your project. Generates 7 files:

| File | Purpose |
|------|---------|
| `app/sso-login-complete/page.tsx` | SSO callback handler |
| `lib/iblai/config.ts` | API URL configuration (supports consolidated `api.domain/lms` pattern) |
| `lib/iblai/storage-service.ts` | localStorage wrapper for the SDK |
| `lib/iblai/auth-utils.ts` | `redirectToAuthSpa()`, `hasNonExpiredAuthToken()`, `handleLogout()` |
| `store/iblai-store.ts` | Redux store with IBL API slices |
| `providers/iblai-providers.tsx` | `AuthProvider` + `TenantProvider` wrapper |
| `app/iblai-styles.css` | SDK component styles |

After running, follow the printed instructions to install dependencies, configure webpack, and set environment variables.

```bash
iblai add auth --platform my-tenant
```

### `iblai add chat`

Adds a self-contained AI chat widget with WebSocket streaming, markdown rendering, session management, and conversation starters. Requires auth to be added first.

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";

<ChatWidget mentorId="your-mentor-id" />
```

### `iblai add profile`

Adds a user profile dropdown using the SDK's `UserProfileDropdown` component.

```tsx
import { IblaiProfileDropdown } from "@/components/iblai/profile-dropdown";

<IblaiProfileDropdown />
```

### `iblai add notification`

Adds a notification bell with unread count badge.

```tsx
import { IblaiNotificationBell } from "@/components/iblai/notification-bell";

<IblaiNotificationBell />
```

### `iblai add mcp`

Adds `.mcp.json` and Claude skill files for AI-assisted development:

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| `iblai-setup.md` | `/iblai-setup` | Full setup from scratch |
| `iblai-add-auth.md` | `/iblai-add-auth` | Step-by-step auth integration |
| `iblai-add-chat.md` | `/iblai-add-chat` | Step-by-step chat integration |
| `iblai-add-profile.md` | `/iblai-add-profile` | Step-by-step profile integration |
| `iblai-add-notification.md` | `/iblai-add-notification` | Step-by-step notifications integration |

### Prerequisites

- `auth` must be added before `chat`, `profile`, or `notifications`
- Project must be a Next.js app with App Router (`app/` directory)
- Files are created in namespaced directories (`lib/iblai/`, `components/iblai/`) to avoid conflicts

### Environment variables

```bash
# Consolidated API (recommended)
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.app
NEXT_PUBLIC_AUTH_URL=https://login.iblai.app
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.app
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.app
NEXT_PUBLIC_MAIN_TENANT_KEY=your-main-platform
```

## What gets generated

The `startapp agent` command creates a complete Next.js 16 application:

### Application structure

```
<app-name>/
├── app/                              # Next.js App Router
│   ├── layout.tsx                    # Root layout (html/body, no providers)
│   ├── globals.css                   # Global styles (Tailwind)
│   ├── (auth)/                       # Auth route group (no AppShell)
│   │   └── sso-login-complete/       # SSO callback handler
│   └── (app)/                        # Authenticated route group (AppShell)
│       ├── layout.tsx                # Wraps children with AppShell/providers
│       ├── page.tsx                  # Home page (redirects to agent)
│       └── platform/[tenantKey]/     # Dynamic tenant routing
│           └── [agentId]/            # Dynamic agent routing
│               └── page.tsx          # Chat interface
├── components/
│   ├── app-shell.tsx                 # Client-side provider wrapper
│   ├── app-sidebar.tsx               # Collapsible sidebar navigation
│   ├── navbar.tsx                    # Top navigation with user dropdown
│   ├── markdown.tsx                  # Markdown renderer for AI responses
│   └── chat/
│       ├── index.tsx                 # Chat orchestrator (WebSocket, state)
│       ├── chat-messages.tsx         # Message display with action buttons
│       ├── chat-input-form.tsx       # Input with file upload
│       ├── welcome.tsx               # Welcome screen
│       └── welcome-v2.tsx            # Welcome screen (alternate layout)
├── components/ui/                    # Radix UI primitives (12 components)
├── hooks/                            # Custom React hooks
├── lib/                              # Utilities and configuration
├── providers/                        # Redux and app providers
├── store/                            # Redux store setup
├── public/env.js                     # Runtime environment config
├── package.json                      # Dependencies
├── next.config.ts                   # Next.js configuration
├── tailwind.config.ts                # Tailwind CSS configuration
├── tsconfig.json                     # TypeScript configuration
└── .env.example                      # Environment variables template
```

### Technology stack

| Category | Technology |
|----------|-----------|
| Framework | Next.js 16 (App Router) |
| UI | React 19, Tailwind CSS, Radix UI |
| State | Redux Toolkit + React-Redux |
| Chat | WebSocket via `@iblai/iblai-js` SDK |
| Auth | SSO with `@iblai/iblai-js/web-utils` |
| Markdown | react-markdown + remark-gfm |
| Notifications | Sonner toast notifications |

### Chat features

- Real-time streaming responses via WebSocket
- "Just a sec..." loading indicator with animated avatar
- Markdown rendering with syntax highlighting
- Copy to clipboard, thumbs up/down rating, share, and retry buttons
- File attachment support
- Session persistence across page reloads
- Scroll-to-bottom with auto-scroll during streaming

### AI-assisted customization

When you provide a `--prompt` flag with an API key, the CLI uses AI to customize these files:

- `app/globals.css` -- color scheme and visual theme
- `app/layout.tsx` -- metadata and page title
- `components/navbar.tsx` -- navigation branding
- `components/app-sidebar.tsx` -- sidebar labels and icons
- `components/chat/welcome.tsx` -- welcome screen copy and prompts
- `components/chat/welcome-v2.tsx` -- alternate welcome layout
- `components/chat/chat-messages.tsx` -- message styling
- `components/chat/chat-input-form.tsx` -- input placeholder text

The AI follows strict rules: it modifies text, colors, and styling but never changes imports, component interfaces, or hook calls.

## CI/CD

- **`build-binaries.yml`** -- Builds PyInstaller binaries for 4 platforms (linux-x64, linux-arm64, darwin-arm64, win32-x64)
- **`publish-npm.yml`** -- Publishes `@iblai/cli` and 4 platform packages to npm
- **`publish-pypi.yml`** -- Publishes `iblai-app-cli` to PyPI

## Install

```bash
git clone https://github.com/iblai/iblai-app-cli.git
cd iblai-app-cli
make -C .iblai install          # End user — installs the CLI
make -C .iblai install-dev      # Developer — includes test/lint deps
```

## Development

All build and development commands are in `.iblai/Makefile`. Run them with `make -C .iblai`:

```bash
make -C .iblai install        # Install the CLI (end user)
make -C .iblai install-dev    # Install with dev dependencies
make -C .iblai test           # Run the test suite (255+ tests)
make -C .iblai lint       # Check code formatting (black + flake8)
make -C .iblai format     # Auto-format code with black
make -C .iblai binary     # Build standalone binary for current platform
make -C .iblai example    # Regenerate the example app at examples/iblai-agent-app
make -C .iblai clean      # Remove build artifacts
make -C .iblai help       # Show all available targets
```

**Tip**: Add a shell alias for convenience:

```bash
alias mk='make -C .iblai'
# Then: mk test, mk binary, mk lint, etc.
```

### Running a specific test

```bash
cd .iblai && pytest tests/test_add_builds.py -v --tb=short
cd .iblai && pytest tests/test_generators.py -k "test_name" -v
```

### Project structure

```
iblai-app-cli/
├── .iblai/                       # Internal machinery (Python package, tests, build tools)
│   ├── iblai/                    # Python package (importable as `iblai`)
│   │   ├── cli.py                # Click CLI entry point
│   │   ├── commands/             # CLI command handlers
│   │   ├── generators/           # App generators (base, agent, add_*)
│   │   └── templates/            # Jinja2 templates, skills, screenshots
│   ├── tests/                    # Test suite (254+ tests)
│   ├── scripts/                  # Build scripts (PyInstaller, example refresh)
│   ├── npm/                      # npm platform binary packages
│   ├── Makefile                  # Development targets
│   ├── pytest.ini                # Test configuration
│   └── pyproject.toml            # Python project config
├── skills/                       # AI assistant skills (categorized)
│   ├── commands/                 # CLI command skills
│   ├── builds/                   # Binary build / publish skills
│   └── internals/                # Template system skills
├── docs/                         # Build dependency guides + screenshots
├── examples/                     # Reference generated app
├── .github/workflows/            # CI/CD (build, release, publish)
├── .claude/ .opencode/ .cursor/  # Tool skill symlinks
├── CLAUDE.md                     # Claude Code guidance
└── README.md
```

## License

MIT -- ibl.ai
