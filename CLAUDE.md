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

Development commands are in `.iblai/Makefile`. Run them with `make -C .iblai`:

```bash
make -C .iblai install    # pip install -e ".iblai/[dev]"
make -C .iblai test       # pytest (254+ tests, 79% coverage)
make -C .iblai lint       # black --check + flake8
make -C .iblai format     # black auto-format
make -C .iblai binary     # PyInstaller build for current platform
make -C .iblai example    # Regenerate examples/iblai-agent-app
make -C .iblai clean      # Remove build artifacts
make -C .iblai help       # Show all available targets

# Run a specific test (from .iblai/ directory)
cd .iblai && pytest tests/test_add_builds.py -v --tb=short
cd .iblai && pytest tests/test_generators.py -k "test_name" -v

# Run the CLI directly (development mode)
iblai --version
iblai startapp agent --platform acme --agent my-id --app-name my-app
iblai add auth
iblai builds dev
```

**Tip**: Add a shell alias for convenience:
```bash
alias mk='make -C .iblai'
# Then: mk test, mk build, mk lint, etc.
```

## Architecture

Internal machinery is in `.iblai/`:

```
.iblai/iblai/
├── cli.py                    # Click entry point — registers startapp, add, tauri
├── config.py                 # .env file loading with stage overrides
├── ai_helper.py              # AI enhancement (Anthropic/OpenAI)
├── project_detector.py       # Detect Next.js App Router projects
├── package_manager.py        # Detect pnpm/yarn/npm/bun from lockfiles
├── next_config_patcher.py    # Regex-based next.config.mjs patching
├── commands/
│   ├── startapp.py           # iblai startapp agent [options]
│   ├── add.py                # iblai add auth|chat|profile|notifications|mcp|tauri
│   └── tauri.py              # iblai builds [passthrough to @tauri-apps/cli]
├── generators/
│   ├── base.py               # BaseGenerator — template rendering, file writing
│   ├── base_app.py           # BaseAppGenerator — generates ~28 shared files
│   ├── agent.py              # AgentAppGenerator — extends base, overlays 4 files
│   ├── add_auth.py           # iblai add auth generator
│   ├── add_chat.py           # iblai add chat generator
│   ├── add_profile.py        # iblai add profile generator
│   ├── add_notifications.py  # iblai add notifications generator
│   ├── add_mcp.py            # iblai add mcp generator
│   └── add_builds.py          # iblai add builds generator + placeholder icon creation
└── templates/
    ├── base/                 # Base template files (package.json, next.config, providers, store)
    ├── agent/                # Agent overrides (page.tsx, config.ts, .env.example, package.json)
    ├── shared/               # Shared templates (layout, SSO, components, e2e, CLAUDE.md)
    ├── add/                  # iblai add templates (auth, chat, profile, notifications)
    ├── tauri/                # Tauri templates (src-tauri/, CI workflows, MSIX scripts)
    ├── skills/               # 13 skill .md files (single source, symlinked to Claude/OpenCode/Cursor)
    └── screenshots/          # 4 .png files referenced by skills
```

### Skills Directory

Skills are stored centrally in `skills/` and symlinked to tool-specific directories:

```
skills/                          # Actual files (edit here)
├── README.md
├── iblai-add-auth.md
└── ...

.claude/skills/<name>.md         -> ../../skills/<name>.md
.opencode/skills/<name>/SKILL.md -> ../../../skills/<name>.md
.cursor/rules/<name>.md          -> ../../skills/<name>.md
```

This structure applies to both the CLI repo itself (6 dev skills) and generated apps (13 integration skills). Screenshots are in `docs/screenshots/`.

### Python Naming Convention

Python package directories cannot contain hyphens — `import iblai-cli` is a syntax error (Python interprets `-` as minus). The names used across the project:

- **Package directory** (importable): `.iblai/iblai/`
- **Distribution name** (pip/PyPI): `iblai-app-cli`
- **CLI command**: `iblai`
- **npm package**: `@iblai/cli`

Do not rename `iblai/` to `iblai-cli/`.

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

Build scripts: `.iblai/scripts/build-binary.sh` (Linux/macOS), `.iblai/scripts/build-binary.ps1` (Windows).

npm distribution: `.iblai/npm/cli/` is the `@iblai/cli` wrapper package with `optionalDependencies` pointing to per-platform packages (`@iblai/cli-linux-x64`, etc.). The `bin/iblai.js` launcher resolves the platform binary at runtime.

## CI/CD Workflows

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| `build-binaries.yml` | `v*` tag, `workflow_dispatch`, `workflow_call` | PyInstaller builds for 5 platforms |
| `release.yml` | `v*` tag | Calls build-binaries, creates GitHub release, calls publish-pypi |
| `publish-pypi.yml` | `workflow_call` (from release), `workflow_dispatch` | Builds sdist+wheel, publishes to PyPI |
| `publish-npm.yml` | `workflow_dispatch` only (manual) | Downloads artifacts by run_id, publishes 6 npm packages from `release` branch |

## Testing

```bash
make -C .iblai test                                       # full suite
cd .iblai && pytest tests/ -v --tb=short                  # same thing
cd .iblai && pytest tests/test_add_builds.py -k "test_generates_icon" -v  # specific
```

Test files (in `.iblai/tests/`):
- `test_cli.py` — CLI help, startapp, add command group
- `test_generators.py` — Agent generator, route groups, components.json
- `test_base_app_generator.py` — Base template, skills, pinned versions, tauri flag
- `test_add_generators.py` — All 7 add generators, src/ dir support, skill counts
- `test_add_builds.py` — Tauri generator, icons, MSIX, CI workflows, next.config patching
- `test_builds_commands.py` — BuildsGroup passthrough, exec prefix detection, prerequisites
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

Available in `skills/` (symlinked to `.claude/skills/`, `.opencode/skills/`, `.cursor/rules/`):

| Skill | Description |
|-------|-------------|
| `/iblai-cli-startapp` | How `iblai startapp` and the generator hierarchy work |
| `/iblai-cli-add-command` | How `iblai add` integrates features into existing projects |
| `/iblai-cli-builds` | How `iblai builds` wraps @tauri-apps/cli with prerequisites |
| `/iblai-cli-build-binary` | Building standalone binaries with PyInstaller |
| `/iblai-cli-publish` | Release workflow: GitHub releases, npm, PyPI |
| `/iblai-cli-templates` | Jinja2 template system: directories, context, conditionals |

THIS PROJECT ALREADY HAS GIT INITIALIZED. DO NOT INITIALIZE GIT.
