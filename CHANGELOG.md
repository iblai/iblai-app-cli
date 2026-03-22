# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-22

### Added

- shadcnspace UI block support. Generated apps now include a `components.json` file that configures the [shadcn/ui CLI](https://ui.shadcn.com/docs/cli), enabling developers to add production-ready UI blocks from [shadcnspace](https://shadcnspace.com) with a single command:
  ```bash
  npx shadcn@latest add @shadcn-space/hero-01
  npx shadcn@latest add @shadcn-space/dashboard-shell-01
  ```
- New `_generate_components_json()` method in `AgentAppGenerator` that renders and writes the `components.json` configuration during app scaffolding.
- Success message after `iblai startapp agent` now includes a "Add UI blocks (shadcnspace)" section with example commands and a link to browse all available blocks.
- 6 new tests for `components.json` generation: file existence, valid JSON, shadcn schema, alias paths, tailwind config, and RSC/TSX flags.

### Changed

- `AgentAppGenerator.generate()` now calls `_generate_components_json()` after `_generate_mcp_config()`.

## [0.1.0] - 2025-06-01

### Added

- Initial release of `iblai-app-cli`.
- `iblai startapp agent` command to scaffold Next.js 15 agent chat applications.
- SSO authentication with IBL Auth SPA.
- WebSocket-based real-time chat with `useAdvancedChat` from `@iblai/iblai-js`.
- AI-assisted customization via `--prompt` with Anthropic and OpenAI support.
- Full app generation: Next.js 15, React 19, Tailwind CSS 4, Redux Toolkit, Radix UI.
