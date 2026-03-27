<div align="center">

<a href="https://ibl.ai"><img src="https://ibl.ai/images/iblai-logo.png" alt="ibl.ai" width="300"></a>

# App CLI

Interactive CLI for scaffolding [ibl.ai](https://ibl.ai) frontend applications.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Install

```bash
pip install iblai-app-cli
# or
npx @iblai/cli
```

## Quick Start

```bash
# Create an agent app with AI chat
iblai startapp agent

# Add features to an existing Next.js app
iblai add auth
iblai add chat
iblai add profile
iblai add notifications

# Add desktop/mobile build support (Tauri v2)
iblai add builds

# Desktop/mobile builds
iblai builds dev
iblai builds build
iblai builds generate-icons logo.png
iblai builds ci-workflow --all
```

## Example App

See [`examples/iblai-agent-app/`](examples/iblai-agent-app/) for a complete reference application with Tauri v2 desktop support, SSO authentication, AI chat, and Playwright E2E tests.

## Skills

AI assistant skills are in [`skills/`](skills/). Invoke with `/` in Claude Code, OpenCode, or Cursor.

Browse all available skills in the [skills README](skills/README.md).

## Development

For development setup, building binaries, running tests, and contributing, see the [development guide](.iblai/README.md).

```bash
# Quick start for developers
make -C .iblai install
make -C .iblai test
make -C .iblai help
```

## License

MIT — [IBL.ai](https://ibl.ai)
