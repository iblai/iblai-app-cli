# CLAUDE.md — CLI Development

This file provides guidance for developing the ibl.ai App CLI tool itself.
For working with generated apps, see the root [CLAUDE.md](../CLAUDE.md).

## Commands

```bash
make -C .iblai install        # Install the CLI (end user)
make -C .iblai install-dev    # Install with dev dependencies
make -C .iblai test           # Run 255+ tests (75% coverage)
make -C .iblai lint           # black --check + flake8
make -C .iblai format         # black auto-format
make -C .iblai binary         # PyInstaller build for current platform
make -C .iblai example        # Regenerate examples/iblai-agent-app
make -C .iblai icons          # Regenerate template icons from logo
make -C .iblai clean          # Remove build artifacts
make -C .iblai help           # Show all targets

# Run a specific test
cd .iblai && pytest tests/test_add_builds.py -v --tb=short
cd .iblai && pytest tests/test_generators.py -k "test_name" -v
```

**Tip**: `alias mk='make -C .iblai'` then `mk test`, `mk example`, etc.

## Architecture

```
.iblai/
├── iblai/                    # Python package (importable as `iblai`)
│   ├── cli.py                # Click entry point — registers startapp, add, builds
│   ├── config.py             # .env file loading with stage overrides
│   ├── ai_helper.py          # AI enhancement (Anthropic/OpenAI)
│   ├── project_detector.py   # Detect Next.js App Router projects
│   ├── package_manager.py    # Detect pnpm/yarn/npm/bun from lockfiles
│   ├── next_config_patcher.py # Regex-based next.config.ts patching
│   ├── commands/
│   │   ├── startapp.py       # iblai startapp agent [options]
│   │   ├── add.py            # iblai add auth|chat|profile|notifications|mcp|builds
│   │   └── builds.py         # iblai builds [passthrough to @tauri-apps/cli]
│   ├── generators/
│   │   ├── base.py           # BaseGenerator — template rendering, file writing
│   │   ├── base_app.py       # BaseAppGenerator — generates ~28 shared files
│   │   ├── agent.py          # AgentAppGenerator — extends base, overlays 4 files
│   │   ├── add_auth.py       # iblai add auth generator
│   │   ├── add_chat.py       # iblai add chat generator
│   │   ├── add_profile.py    # iblai add profile generator
│   │   ├── add_notifications.py # iblai add notification generator
│   │   ├── add_mcp.py        # iblai add mcp generator
│   │   └── add_builds.py     # iblai add builds generator + icon creation
│   └── templates/
│       ├── base/             # Base template files
│       ├── agent/            # Agent overrides (4 files)
│       ├── shared/           # Shared templates (layout, SSO, components, e2e)
│       ├── add/              # iblai add templates
│       ├── tauri/            # Tauri templates (src-tauri/, CI, MSIX)
│       ├── skills/           # 13 skill .md files (4 categories)
│       ├── screenshots/      # 4 .png files referenced by skills
│       └── icons/            # Pre-generated ibl.ai logo icons
├── tests/                    # 255+ tests
├── scripts/                  # Build scripts
├── npm/                      # npm platform binary packages
├── docs/                     # Build deps, logo, screenshots
├── skills/                   # 6 CLI dev skills (3 categories)
├── Makefile
├── pyproject.toml
└── pytest.ini
```

## Python Naming Convention

Python package directories cannot contain hyphens. The names are:

- **Package directory**: `.iblai/iblai/`
- **Distribution name** (PyPI): `iblai-app-cli`
- **CLI command**: `iblai`
- **npm package**: `@iblai/cli`

Do not rename `iblai/` to `iblai-cli/`.

## Generator Hierarchy

```
BaseGenerator (base.py)
  - Template rendering (Jinja2), file writing, static file copying
  - Context: app_name, platform_key, mentor_id, has_mentor_id, builds
  └── BaseAppGenerator (base_app.py)
        - Generates ~28 files from shared/ + base/ templates
        - get_context() returns {app_name, platform_key, builds}
        └── AgentAppGenerator (agent.py)
              - Calls super().generate(), overlays 4 agent-specific files
              - get_context() adds mentor_id, has_mentor_id
```

## Template Context Variables

| Variable | Type | Set by | Used in |
|----------|------|--------|---------|
| `app_name` | str | All generators | package.json, layout, config, Cargo.toml |
| `platform_key` | str | All generators | .env.example, config.ts |
| `mentor_id` | str | AgentAppGenerator | .env.example, config.ts, page.tsx |
| `has_mentor_id` | bool | AgentAppGenerator | CLAUDE.md conditionals |
| `builds` | bool | BaseAppGenerator | next.config.ts, package.json, CLAUDE.md |

## Binary Distribution

5 platforms via PyInstaller:

| Target | Runner | Binary |
|--------|--------|--------|
| `linux-x64` | `ubuntu-22.04` | `iblai` |
| `linux-arm64` | `ubuntu-22.04-arm` | `iblai` |
| `darwin-arm64` | `macos-14` | `iblai` |
| `win32-x64` | `windows-latest` | `iblai.exe` |
| `win32-arm64` | `windows-11-arm` | `iblai.exe` |

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-binaries.yml` | `v*` tag, `workflow_dispatch`, `workflow_call` | PyInstaller builds |
| `release.yml` | `v*` tag | GitHub release + PyPI publish |
| `publish-pypi.yml` | `workflow_call`, `workflow_dispatch` | PyPI |
| `publish-npm.yml` | `workflow_dispatch` only | npm (manual, from `release` branch) |

## Testing

255+ tests, 75% coverage. Test files in `.iblai/tests/`:
- `test_cli.py`, `test_generators.py`, `test_base_app_generator.py`
- `test_add_generators.py`, `test_add_builds.py`, `test_builds_commands.py`
- `test_distribution.py`, `test_project_detector.py`, `test_package_manager.py`
- `test_next_config_patcher.py`, `test_config.py`, `test_ai_helper.py`

## Git Conventions

**Branches**: `feat/`, `fix/`, `chore/`, `docs/`

**Commits**: Conventional Commits — `feat(scope): ...`, `fix: ...`, `chore: ...`

## Skills (CLI Dev)

6 skills in `.iblai/skills/` (symlinked to root `.claude/skills/`):

| Skill | Description |
|-------|-------------|
| `/iblai-cli-startapp` | `iblai startapp` and the generator hierarchy |
| `/iblai-cli-add-command` | `iblai add` integrates features into existing projects |
| `/iblai-cli-builds` | `iblai builds` wraps @tauri-apps/cli |
| `/iblai-cli-build-binary` | Building standalone binaries with PyInstaller |
| `/iblai-cli-publish` | Release workflow: GitHub releases, npm, PyPI |
| `/iblai-cli-templates` | Jinja2 template system: directories, context, conditionals |

THIS PROJECT ALREADY HAS GIT INITIALIZED. DO NOT INITIALIZE GIT.
