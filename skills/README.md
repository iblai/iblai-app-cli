# Skills

AI assistant skills for developing the iblai-app-cli tool itself.
Invoke them with `/` in Claude Code, OpenCode, or Cursor.

## Categories

### Commands

| Skill | Description |
|-------|-------------|
| `/iblai-cli-startapp` | How `iblai startapp` and the generator hierarchy work |
| `/iblai-cli-add-command` | How `iblai add` integrates features into existing projects |
| `/iblai-cli-tauri` | How `iblai tauri` wraps @tauri-apps/cli with prerequisites |

### Builds

| Skill | Description |
|-------|-------------|
| `/iblai-cli-build-binary` | Building standalone binaries with PyInstaller |
| `/iblai-cli-publish` | Release workflow: GitHub releases, npm, PyPI |

### Internals

| Skill | Description |
|-------|-------------|
| `/iblai-cli-templates` | Jinja2 template system: directories, context, conditionals |

## Tool Integration

Skills are symlinked to tool-specific directories:

- **Claude Code**: `.claude/skills/<name>.md`
- **OpenCode**: `.opencode/skills/<name>/SKILL.md`
- **Cursor**: `.cursor/rules/<name>.md`

All symlinks point back to this directory. Edit the files here — changes are reflected everywhere.

## Windows Note

Symlinks require Developer Mode or Administrator privileges on Windows.
If skills appear as small text files instead of markdown content, enable Developer Mode:

```
Settings > Update & Security > For developers > Developer Mode: ON
```

Then re-clone with: `git clone -c core.symlinks=true <url>`
