# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-22

### Added

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
- 18 new tests: 8 for `config.py` (`.env` loading, stage overrides, env precedence) and 10 for `AIHelper` (custom model/temperature/max_tokens, default values, error handling).

### Changed

- `AIHelper` now accepts `model`, `temperature`, and `max_tokens` parameters in its constructor instead of using hardcoded values. Default model names, temperatures, and token limits are now class constants.
- `BaseGenerator.__init__()` accepts and passes `ai_model`, `ai_temperature`, `ai_max_tokens` through to `AIHelper`.
- `cli.py` calls `load_config()` at import time so `.env` values are in `os.environ` before Click parses options.
- Interactive prompts for platform key, agent ID, and app name are now skipped when values are provided via flags, environment variables, or `.env` files.

### Fixed

- Hardcoded `"sba-agent-app"` in `package.json.j2` and `layout.tsx.j2` templates replaced with `{{ app_name }}`.
- Test option names corrected: `--platform-key` to `--platform`, `--mentor-id` to `--agent`.
- Test assertion for `next.config.js` corrected to `next.config.mjs`.
- Added `clean_env` test fixture to prevent host AI API keys from leaking into test runs.

## [0.1.0] - 2025-06-01

### Added

- Initial release of `iblai-app-cli`.
- `iblai startapp agent` command to scaffold Next.js 15 agent chat applications.
- SSO authentication with IBL Auth SPA.
- WebSocket-based real-time chat with `useAdvancedChat` from `@iblai/iblai-js`.
- AI-assisted customization via `--prompt` with Anthropic and OpenAI support.
- Full app generation: Next.js 15, React 19, Tailwind CSS 4, Redux Toolkit, Radix UI.
