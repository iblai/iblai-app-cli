# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-22

### Added

- `iblai startapp base` template -- minimal Next.js app with IBL.ai SSO auth, Redux store, and providers. No chat UI, no sidebar, no agent routes. A blank canvas for custom development with pinned dependency versions. Uses shared templates (`templates/shared/`) with the agent template for common files (tsconfig, postcss, gitignore, SSO callback, providers, etc.) and template-specific files (`templates/base/`) for the simplified package.json, store, providers, config, and home page.
- `iblai add` command group for integrating IBL.ai features into existing Next.js apps:
  - `iblai add auth`: SSO authentication -- generates SSO callback page, config, storage service, auth utilities, Redux store, provider wrapper, and SDK styles (7 files).
  - `iblai add chat`: AI chat widget -- full-featured component with WebSocket streaming, markdown rendering (react-markdown + remark-gfm), session management with localStorage persistence, conversation starters, copy-to-clipboard, scroll management, and agent-template-matching styling.
  - `iblai add profile`: User profile dropdown using the SDK's `UserProfileDropdown` component with tenant switching and logout.
  - `iblai add notifications`: Notification bell with unread count badge using the SDK's `NotificationDropdown` component.
  - `iblai add mcp`: MCP server configuration (`.mcp.json`) and 5 Claude skill files for AI-assisted integration (`.claude/skills/`).
- Project detector (`project_detector.py`) that identifies Next.js App Router projects, detects `src/` directory layout, and checks for existing TypeScript, Redux, and `@iblai/iblai-js` dependencies.
- 5 Claude skills for AI-assisted integration:
  - `/iblai-setup` -- Full setup from scratch
  - `/iblai-add-auth` -- Step-by-step auth integration with MCP tool calls
  - `/iblai-add-chat` -- Chat widget integration
  - `/iblai-add-profile` -- Profile dropdown integration
  - `/iblai-add-notifications` -- Notification bell integration
- `iblai-styles.css` template that imports SDK base styles (`@iblai/iblai-js/web-containers/styles`) and scans SDK components for Tailwind class generation.
- Consolidated API URL support via `NEXT_PUBLIC_API_BASE_URL` (e.g., `https://api.iblai.org` derives `/lms`, `/dm`, `/axd` path prefixes). Falls back to subdomain pattern via `NEXT_PUBLIC_PLATFORM_BASE_DOMAIN`.
- shadcnspace UI block support. Generated apps include a `components.json` file that configures the [shadcn/ui CLI](https://ui.shadcn.com/docs/cli), enabling developers to add production-ready UI blocks from [shadcnspace](https://shadcnspace.com) with a single command:
  ```bash
  npx shadcn@latest add @shadcn-space/hero-01
  npx shadcn@latest add @shadcn-space/dashboard-shell-01
  ```
- `.env` file configuration support. The CLI now loads configuration from `.env` and `.env.{stage}` files in the current directory, with a clear priority chain: CLI flags > system env vars > `.env.{stage}` > `.env` > interactive prompts.
- New `iblai_cli/config.py` module implementing the `.env` loading logic with `python-dotenv`.
- Six new CLI options for `iblai startapp`:
  - `--app-name` (`IBLAI_APP_NAME`) -- set the app name non-interactively
  - `--env-file` -- path to a custom `.env` file
  - `--stage` (`DEV_STAGE`) -- load `.env.{stage}` overrides (e.g., `.env.production`)
  - `--ai-model` (`IBLAI_AI_MODEL`) -- override the default AI model
  - `--ai-temperature` (`IBLAI_AI_TEMPERATURE`) -- set AI generation temperature (0.0-2.0)
  - `--ai-max-tokens` (`IBLAI_AI_MAX_TOKENS`) -- set AI max output tokens
- Environment variable mappings (`envvar=`) added to all existing CLI options: `IBLAI_PLATFORM_KEY`, `IBLAI_AGENT_ID`, `IBLAI_OUTPUT_DIR`, `IBLAI_AI_PROVIDER`, `IBLAI_PROMPT`.
- `.env.example` file documenting all 12 supported environment variables.
- `python-dotenv>=1.0.0` added to project dependencies.
- 6 new tests for `components.json` generation: file existence, valid JSON, shadcn schema, alias paths, tailwind config, and RSC/TSX flags.
- 18 new tests: 8 for `config.py` (`.env` loading, stage overrides, env precedence) and 10 for `AIHelper` (custom model/temperature/max_tokens, default values, error handling).
- 44 new tests covering project detection, all 5 add generators, route group structure, src/ directory support, and CLI command registration.

### Changed

- Agent template restructured to use Next.js route groups:
  - `app/(auth)/sso-login-complete/` -- SSO callback runs outside auth providers (prevents deadlock).
  - `app/(app)/` -- All authenticated routes wrapped by `AppShell` with providers.
  - Root `app/layout.tsx` now contains only html/body/font/Toaster -- no `AppShell`.
- `hasNonExpiredAuthToken()` returns `false` (not `true`) when no token exists, enabling proper auth redirects for fresh sessions.
- Agent template config (`lib/config.ts.j2`) supports consolidated API URL pattern matching mentorai, with backward compatibility for individual `NEXT_PUBLIC_LMS_URL` / `NEXT_PUBLIC_DM_URL` / `NEXT_PUBLIC_AXD_URL` overrides.
- `.env.example` uses consolidated API URL pattern with `.iblai.org` defaults instead of separate URLs with `.iblai.app` defaults.
- `AIHelper` now accepts `model`, `temperature`, and `max_tokens` parameters in its constructor instead of using hardcoded values. Default model names, temperatures, and token limits are now class constants.
- `BaseGenerator.__init__()` accepts and passes `ai_model`, `ai_temperature`, `ai_max_tokens` through to `AIHelper`.
- `cli.py` calls `load_config()` at import time so `.env` values are in `os.environ` before Click parses options.
- Interactive prompts for platform key, agent ID, and app name are now skipped when values are provided via flags, environment variables, or `.env` files.

### Fixed

- SSO callback deadlock: SSO page was wrapped by `AuthProvider` which blocked rendering before tokens were stored. Resolved by moving SSO to `(auth)` route group outside the provider tree.
- `sidebarInnerClassName` invalid prop removed from `app-sidebar.tsx.j2` (merged into `className`).
- `AXD_TOKEN_EXPIRES` key mapping corrected in agent template SSO callback (`"axd_token_expires"` instead of `LOCAL_STORAGE_KEYS.AXD_TOKEN_KEY`).
- `defaultRedirectPath` double-brace JSX template rendering bug fixed (`{{ '{{' }}` changed to `{{ '{' }}`).
- `UserProfileDropdown` missing required `onTenantUpdate` prop added to profile dropdown template.
- Hardcoded `"sba-agent-app"` in `package.json.j2` and `layout.tsx.j2` templates replaced with `{{ app_name }}`.
- Test option names corrected: `--platform-key` to `--platform`, `--mentor-id` to `--agent`.
- Test assertion for `next.config.js` corrected to `next.config.mjs`.
- Added `clean_env` test fixture to prevent host AI API keys from leaking into test runs.
- PyInstaller binary builds fixed: `pyproject.toml` switched from explicit package list to `packages.find` auto-discovery, and `commands/startapp.py` indentation corrected.
- Dropped `macos-13` (darwin-x64) from CI build matrix -- GitHub Actions no longer supports that runner.

## [0.1.0] - 2025-06-01

### Added

- Initial release of `iblai-app-cli`.
- `iblai startapp agent` command to scaffold Next.js 15 agent chat applications.
- SSO authentication with IBL Auth SPA.
- WebSocket-based real-time chat with `useAdvancedChat` from `@iblai/iblai-js`.
- AI-assisted customization via `--prompt` with Anthropic and OpenAI support.
- Full app generation: Next.js 15, React 19, Tailwind CSS 4, Redux Toolkit, Radix UI.
