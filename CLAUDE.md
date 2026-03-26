# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**iblai-app-cli** — CLI tool for scaffolding IBL.ai frontend applications. Generates Next.js 15 apps with SSO authentication, Redux Toolkit store, Tauri v2 desktop shell, and pre-built SDK components. Also adds IBL.ai features to existing Next.js apps via `iblai add`.

- **Language**: Python 3.11
- **CLI framework**: Click 8
- **Templates**: Jinja2 3
- **UI**: Rich 13 (terminal formatting), Inquirer 3 (interactive prompts)
- **AI**: Anthropic + OpenAI SDKs for `--prompt` enhancement
- **Distribution**: PyPI (`iblai-app-cli`) + npm (`@iblai/cli` with per-platform binaries)

## Commands

```bash
# Development
make install          # pip install -e ".[dev]"
make test             # pytest tests/ -v --tb=short
make lint             # black --check + flake8
make format           # black auto-format
make clean            # remove build artifacts

# Run a single test file or specific test
pytest tests/test_add_tauri.py -v --tb=short
pytest tests/test_generators.py -k "test_name" -v

# Build standalone binary for current platform
make binary           # calls scripts/build-binary.sh

# Run the CLI directly (development mode)
iblai --version
iblai startapp agent --platform acme --agent my-id --app-name my-app
iblai add auth
iblai tauri dev
```

## Architecture

```
iblai_cli/
├── cli.py                    # Click entry point — registers startapp, add, tauri
├── config.py                 # .env file loading with stage overrides
├── ai_helper.py              # AI enhancement (Anthropic/OpenAI)
├── project_detector.py       # Detect Next.js App Router projects
├── package_manager.py        # Detect pnpm/yarn/npm/bun from lockfiles
├── next_config_patcher.py    # Regex-based next.config.mjs patching
├── commands/
│   ├── startapp.py           # iblai startapp agent [options]
│   ├── add.py                # iblai add auth|chat|profile|notifications|mcp|tauri
│   └── tauri.py              # iblai tauri [passthrough to @tauri-apps/cli]
├── generators/
│   ├── base.py               # BaseGenerator — template rendering, file writing
│   ├── base_app.py           # BaseAppGenerator — generates ~28 shared files
│   ├── agent.py              # AgentAppGenerator — extends base, overlays 4 files
│   ├── add_auth.py           # iblai add auth generator
│   ├── add_chat.py           # iblai add chat generator
│   ├── add_profile.py        # iblai add profile generator
│   ├── add_notifications.py  # iblai add notifications generator
│   ├── add_mcp.py            # iblai add mcp generator
│   └── add_tauri.py          # iblai add tauri generator + placeholder icon creation
└── templates/
    ├── base/                 # Base template files (package.json, next.config, providers, store)
    ├── agent/                # Agent overrides (page.tsx, config.ts, .env.example, package.json)
    ├── shared/               # Shared templates (layout, SSO, components, e2e, CLAUDE.md)
    ├── add/                  # iblai add templates (auth, chat, profile, notifications)
    ├── tauri/                # Tauri templates (src-tauri/, CI workflows, MSIX scripts)
    ├── skills/               # 13 Claude skill .md files + screenshots
    └── opencode-skills/      # 13 OpenCode skill directories (SKILL.md + screenshots)
```

### Python Naming Convention

The package directory is `iblai_cli/` (underscores), not `iblai-cli/` (hyphens). This is a hard Python requirement — `import iblai_cli` works, but `import iblai-cli` is a syntax error (Python interprets `-` as minus). The convention is:

- **Package directory** (importable): underscores → `iblai_cli/`
- **Distribution name** (pip/PyPI): hyphens → `iblai-app-cli`
- **CLI command**: hyphens → `iblai`

Do not rename `iblai_cli/` to `iblai-cli/`.

### Generator Hierarchy

```
BaseGenerator (base.py)
  - Template rendering (Jinja2), file writing, static file copying
  - Context: app_name, platform_key, mentor_id, has_mentor_id, tauri
  └── BaseAppGenerator (base_app.py)
        - Generates ~28 files from shared/ + base/ templates
        - Own Jinja2 Environment with FileSystemLoader [base/, shared/, add/]
        - get_context() returns {app_name, platform_key, tauri}
        └── AgentAppGenerator (agent.py)
              - Calls super().generate(), then overlays 4 agent-specific files
              - Own Environment with FileSystemLoader [agent/, base/, shared/, add/]
              - get_context() adds mentor_id, has_mentor_id
```

### Template Context Variables

| Variable | Type | Set by | Used in |
|----------|------|--------|---------|
| `app_name` | str | All generators | package.json, layout, config, Cargo.toml, tauri.conf.json |
| `platform_key` | str | All generators | .env.example, config.ts |
| `mentor_id` | str | AgentAppGenerator | .env.example, config.ts, page.tsx |
| `has_mentor_id` | bool | AgentAppGenerator | CLAUDE.md conditionals |
| `tauri` | bool | BaseAppGenerator | next.config.mjs, package.json, CLAUDE.md |

## Binary Distribution

5 platforms built via PyInstaller:

| Target | Runner | Binary |
|--------|--------|--------|
| `linux-x64` | `ubuntu-22.04` | `iblai` |
| `linux-arm64` | `ubuntu-22.04-arm` | `iblai` |
| `darwin-arm64` | `macos-14` | `iblai` |
| `win32-x64` | `windows-latest` | `iblai.exe` |
| `win32-arm64` | `windows-11-arm` | `iblai.exe` |

Build scripts: `scripts/build-binary.sh` (Linux/macOS), `scripts/build-binary.ps1` (Windows).

npm distribution: `npm/cli/` is the `@iblai/cli` wrapper package with `optionalDependencies` pointing to per-platform packages (`@iblai/cli-linux-x64`, etc.). The `bin/iblai.js` launcher resolves the platform binary at runtime.

## CI/CD Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `build-binaries.yml` | `v*` tag, `workflow_dispatch`, `workflow_call` | PyInstaller builds for 5 platforms |
| `release.yml` | `v*` tag | Calls build-binaries, creates GitHub release, calls publish-pypi |
| `publish-pypi.yml` | `workflow_call` (from release), `workflow_dispatch` | Builds sdist+wheel, publishes to PyPI |
| `publish-npm.yml` | `workflow_dispatch` only (manual) | Downloads artifacts by run_id, publishes 6 npm packages from `release` branch |

## Testing

```bash
make test                    # 251+ tests, 78% coverage
pytest tests/ -v --tb=short  # same thing
pytest tests/test_add_tauri.py -k "test_generates_icon" -v  # specific test
```

Test files:
- `test_cli.py` — CLI help, startapp, add command group
- `test_generators.py` — Agent generator, route groups, components.json
- `test_base_app_generator.py` — Base template, skills, pinned versions, tauri flag
- `test_add_generators.py` — All 7 add generators, src/ dir support, skill counts
- `test_add_tauri.py` — Tauri generator, icons, MSIX, CI workflows, next.config patching
- `test_tauri_commands.py` — TauriGroup passthrough, exec prefix detection, prerequisites
- `test_distribution.py` — npm packages, workflows, PyInstaller, pyproject.toml
- `test_project_detector.py` — Next.js detection, src/ layout
- `test_package_manager.py` — pnpm/yarn/npm/bun detection
- `test_next_config_patcher.py` — webpack, globals.css, .env.local, store patching
- `test_config.py` — .env loading, stage overrides
- `test_ai_helper.py` — model/temperature/max_tokens params

## Git Conventions

**Branches**: `feat/<name>`, `fix/<name>`, `chore/<name>`, `docs/<name>`

**Commits**: Conventional Commits format:
```
feat(tauri): add Windows MSIX build script
fix(generators): pass tauri flag through BaseAppGenerator context
chore: align Python version to 3.11.15
docs: add per-platform build dependency guides
```

## Skills

Available in `.claude/skills/` (invoke with `/` in Claude Code):

| Skill | Description |
|-------|-------------|
| `/iblai-cli-startapp` | How `iblai startapp` and the generator hierarchy work |
| `/iblai-cli-add-command` | How `iblai add` integrates features into existing projects |
| `/iblai-cli-tauri` | How `iblai tauri` wraps @tauri-apps/cli with prerequisites |
| `/iblai-cli-build-binary` | Building standalone binaries with PyInstaller |
| `/iblai-cli-publish` | Release workflow: GitHub releases, npm, PyPI |
| `/iblai-cli-templates` | Jinja2 template system: directories, context, conditionals |

THIS PROJECT ALREADY HAS GIT INITIALIZED. DO NOT INITIALIZE GIT.
