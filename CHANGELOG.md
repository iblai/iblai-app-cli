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
- 44 new tests covering project detection, all 5 add generators, route group structure, src/ directory support, and CLI command registration.

### Changed

- Agent template restructured to use Next.js route groups:
  - `app/(auth)/sso-login-complete/` -- SSO callback runs outside auth providers (prevents deadlock).
  - `app/(app)/` -- All authenticated routes wrapped by `AppShell` with providers.
  - Root `app/layout.tsx` now contains only html/body/font/Toaster -- no `AppShell`.
- `hasNonExpiredAuthToken()` returns `false` (not `true`) when no token exists, enabling proper auth redirects for fresh sessions.
- Agent template config (`lib/config.ts.j2`) supports consolidated API URL pattern matching mentorai, with backward compatibility for individual `NEXT_PUBLIC_LMS_URL` / `NEXT_PUBLIC_DM_URL` / `NEXT_PUBLIC_AXD_URL` overrides.
- `.env.example` uses consolidated API URL pattern with `.iblai.org` defaults instead of separate URLs with `.iblai.app` defaults.

### Fixed

- SSO callback deadlock: SSO page was wrapped by `AuthProvider` which blocked rendering before tokens were stored. Resolved by moving SSO to `(auth)` route group outside the provider tree.
- `sidebarInnerClassName` invalid prop removed from `app-sidebar.tsx.j2` (merged into `className`).
- `AXD_TOKEN_EXPIRES` key mapping corrected in agent template SSO callback (`"axd_token_expires"` instead of `LOCAL_STORAGE_KEYS.AXD_TOKEN_KEY`).
- `defaultRedirectPath` double-brace JSX template rendering bug fixed (`{{ '{{' }}` changed to `{{ '{' }}`).
- `UserProfileDropdown` missing required `onTenantUpdate` prop added to profile dropdown template.

## [0.1.0] - 2025-06-01

### Added

- Initial release of `iblai-app-cli`.
- `iblai startapp agent` command to scaffold Next.js 15 agent chat applications.
- SSO authentication with IBL Auth SPA.
- WebSocket-based real-time chat with `useAdvancedChat` from `@iblai/iblai-js`.
- AI-assisted customization via `--prompt` with Anthropic and OpenAI support.
- Full app generation: Next.js 15, React 19, Tailwind CSS 4, Redux Toolkit, Radix UI.
