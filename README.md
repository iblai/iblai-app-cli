<div align="center">

<a href="https://ibl.ai"><img src="https://ibl.ai/images/iblai-logo.png" alt="ibl.ai" width="300"></a>

# App CLI

Interactive CLI for scaffolding [ibl.ai](https://ibl.ai) frontend applications. Generates production-ready Next.js apps with chat interfaces, authentication, and full integration with the ibl.ai platform SDK.

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
- **An ibl.ai platform account** with a tenant and at least one agent configured

### Dependencies installed automatically

The following are installed as Python package dependencies:

- **click** (>= 8.0) -- CLI framework
- **jinja2** (>= 3.0) -- template rendering engine
- **rich** (>= 13.0) -- terminal formatting and UI
- **inquirer** (>= 3.0) -- interactive prompts
- **anthropic** (>= 0.40) -- AI-assisted generation (optional)
- **openai** (>= 1.0) -- AI-assisted generation (optional)

## Install

### npx (Node.js -- no Python required)

```bash
npx @iblai/cli startapp agent
```

The npm package wraps a pre-built binary, so no Python installation is needed.

### uvx (Python -- recommended)

```bash
uvx iblai-app-cli startapp agent
```

Or install globally:

```bash
uv tool install iblai-app-cli
iblai startapp agent
```

### pipx (Python)

```bash
pipx run --spec iblai-app-cli iblai startapp agent
```

Or install globally:

```bash
pipx install iblai-app-cli
iblai startapp agent
```

### pip (from source)

```bash
git clone git@github.com:iblai/iblai-app-cli.git
cd iblai-app-cli
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

### Verify installation

```bash
iblai --version
```

### Distribution channels

| Channel | Command | Requires |
|---------|---------|----------|
| **npx** | `npx @iblai/cli startapp agent` | Node.js 18+ |


The npx distribution uses platform-specific binary packages (`@iblai/cli-{os}-{arch}`) built with PyInstaller. npm installs only the binary for your OS/architecture via `optionalDependencies`.

### CI/CD

Releases are automated via GitHub Actions:

- **`build-binaries.yml`** -- Builds PyInstaller binaries for Linux (x64, arm64), macOS (Intel, Apple Silicon), and Windows (x64)
- **`publish-npm.yml`** -- Publishes `@iblai/cli` and 5 platform packages to npm
- **`publish-pypi.yml`** -- Publishes `iblai-app-cli` to PyPI

Required repository secrets: `NPM_TOKEN`, `PYPI_TOKEN`

## Usage

Run `iblai --help` to see all available commands.

```
Usage: iblai [OPTIONS] COMMAND [ARGS]...

  IBL.ai CLI - Quickly scaffold IBL.ai applications.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  startapp  Create a new IBL.ai application from a template.
```

### `iblai startapp agent`

Scaffolds a complete Next.js 15 agent chat application with SSO authentication, Redux state management, and full ibl.ai SDK integration.

```bash
iblai startapp agent
```

Interactive wizard that walks you through:

1. **Platform key** -- your ibl.ai tenant identifier
2. **Agent ID** -- the agent/mentor to connect to (optional, can be set later)
3. **App name** -- directory name for the generated project

#### Options

```
Options:
  --platform, -p TEXT           Platform key (tenant identifier)
  --agent, -a TEXT              Agent ID
  --app-name TEXT               App name (directory and package.json name)
  --output, -o PATH             Output directory (default: current directory)
  --openai-key TEXT             OpenAI API key for AI-assisted customization
  --anthropic-key TEXT          Anthropic API key for AI-assisted customization
  --ai-provider [openai|anthropic]  AI provider to use
  --ai-model TEXT               AI model override (e.g., claude-sonnet-4-20250514)
  --ai-temperature FLOAT        AI temperature (0.0-2.0)
  --ai-max-tokens INTEGER       AI max tokens for generation
  --prompt, -P TEXT             Natural language prompt to customize the app
  --env-file PATH               Path to a custom .env file
  --stage TEXT                  Stage name to load .env.{stage} overrides
  --help                        Show this message and exit
```

#### Configuration via `.env` files

Instead of passing all options as CLI flags, you can create a `.env` file:

```bash
# .env
IBLAI_PLATFORM_KEY=acme
IBLAI_APP_NAME=my-app
IBLAI_AGENT_ID=my-agent-123
ANTHROPIC_API_KEY=sk-ant-...
IBLAI_PROMPT=Make this a kids learning assistant
```

Then run with no flags:

```bash
iblai startapp agent
```

Stage-specific overrides are supported via `.env.{stage}` files:

```bash
# .env.production
IBLAI_PLATFORM_KEY=acme-prod
IBLAI_AGENT_ID=prod-agent

# Load with:
iblai startapp agent --stage production
# Or set DEV_STAGE=production in your environment
```

**Resolution priority** (highest wins):

```
CLI flags > System env vars > .env.{DEV_STAGE} > .env > interactive prompts
```

#### Environment variables

| Variable | CLI Flag | Description |
|----------|----------|-------------|
| `IBLAI_PLATFORM_KEY` | `--platform` | Platform/tenant key |
| `IBLAI_AGENT_ID` | `--agent` | Agent/mentor ID |
| `IBLAI_APP_NAME` | `--app-name` | App name |
| `IBLAI_OUTPUT_DIR` | `--output` | Output directory |
| `IBLAI_AI_PROVIDER` | `--ai-provider` | AI provider (openai/anthropic) |
| `IBLAI_AI_MODEL` | `--ai-model` | AI model override |
| `IBLAI_AI_TEMPERATURE` | `--ai-temperature` | AI temperature |
| `IBLAI_AI_MAX_TOKENS` | `--ai-max-tokens` | AI max tokens |
| `OPENAI_API_KEY` | `--openai-key` | OpenAI API key |
| `ANTHROPIC_API_KEY` | `--anthropic-key` | Anthropic API key |
| `IBLAI_PROMPT` | `--prompt` | Enhancement prompt |
| `DEV_STAGE` | `--stage` | Stage name for `.env.{stage}` |

#### Examples

```bash
# Interactive mode (prompts for all required values)
iblai startapp agent

# Non-interactive with platform and agent
iblai startapp agent --platform acme --agent my-agent-123

# Non-interactive with app name (skips prompt)
iblai startapp agent --platform acme --app-name my-app

# Generate into a specific directory
iblai startapp agent --platform acme --output ./projects

# AI-assisted customization with model override
iblai startapp agent --platform acme \
  --anthropic-key sk-ant-... \
  --ai-model claude-sonnet-4-20250514 \
  --ai-temperature 0.5 \
  --prompt "Make this a kids learning assistant with bright colors"

# Using a custom .env file
iblai startapp agent --env-file ./config/.env

# Using stage-specific config
DEV_STAGE=production iblai startapp agent
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
# After pnpm install:
npx shadcn@latest add @shadcn-space/hero-01
npx shadcn@latest add @shadcn-space/pricing-01
npx shadcn@latest add @shadcn-space/dashboard-shell-01
```

Browse all available blocks at [shadcnspace.com/blocks](https://shadcnspace.com/blocks).

The blocks are copied into your project as source code (not a dependency) -- you have full ownership to customize them.

## What gets generated

The `startapp agent` command creates a complete Next.js 15 application:

### Application structure

```
<app-name>/
├── app/                              # Next.js App Router
│   ├── layout.tsx                    # Root layout with providers
│   ├── page.tsx                      # Home page (redirects to agent)
│   ├── globals.css                   # Global styles (Tailwind)
│   ├── sso-login-complete/           # SSO callback handler
│   └── platform/[tenantKey]/         # Dynamic tenant routing
│       └── [agentId]/                # Dynamic agent routing
│           └── page.tsx              # Chat interface
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
├── components.json                   # shadcn/ui CLI configuration
├── package.json                      # Dependencies
├── next.config.mjs                   # Next.js configuration
├── tailwind.config.ts                # Tailwind CSS configuration
├── tsconfig.json                     # TypeScript configuration
└── .env.example                      # Environment variables template
```

### Technology stack

| Category | Technology |
|----------|-----------|
| Framework | Next.js 15 (App Router) |
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

## Development

### Running tests

```bash
uv sync --extra dev
uv run pytest tests/ -v
```

With coverage:

```bash
uv run pytest tests/ --cov=iblai_cli --cov-report=term-missing
```

### Project structure

```
iblai-app-cli/
├── iblai_cli/
│   ├── cli.py                    # Click CLI entry point
│   ├── ai_helper.py              # AI enhancement (Anthropic/OpenAI)
│   ├── commands/
│   │   └── startapp.py           # startapp command handler
│   ├── generators/
│   │   ├── base.py               # BaseGenerator (template rendering)
│   │   └── agent.py              # AgentAppGenerator (48+ files)
│   └── templates/
│       └── agent/                # Jinja2 templates for agent apps
├── tests/
│   ├── test_cli.py               # CLI integration tests
│   └── test_generators.py        # Generator unit tests
└── pyproject.toml
```

## License

MIT -- ibl.ai
