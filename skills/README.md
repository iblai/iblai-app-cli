# Skills

AI assistant skills for Claude Code, OpenCode, and Cursor.
Invoke them with `/` in your AI assistant.

## Categories

### Setup

| Skill | Description |
|-------|-------------|
| `/iblai-setup` | What's set up, env config, localStorage keys, MCP tools |

### Components

| Skill | Description |
|-------|-------------|
| `/iblai-add-auth` | Add SSO authentication |
| `/iblai-add-chat` | AI chat widget + customization |
| `/iblai-add-profile` | Profile dropdown + full settings page |
| `/iblai-add-account` | Organization/account settings |
| `/iblai-add-analytics` | Analytics dashboard |
| `/iblai-add-notifications` | Notification bell + center page |
| `/iblai-add-component` | Generic guide for any SDK component |
| `/iblai-add-shadcn-component` | Add shadcnspace blocks with ibl.ai brand consistency |

### Builds

| Skill | Description |
|-------|-------------|
| `/iblai-build-windows-msix` | Windows MSIX build for test and release |
| `/iblai-generate-icons` | Generate all Tauri icon sizes from a source image |

### Testing

| Skill | Description |
|-------|-------------|
| `/iblai-add-test` | Playwright E2E test patterns |

## Tool Integration

Skills are symlinked to tool-specific directories:

- **Claude Code**: `.claude/skills/<name>.md`
- **OpenCode**: `.opencode/skills/<name>/SKILL.md`
- **Cursor**: `.cursor/rules/<name>.md`

All symlinks point back to this `skills/` directory. Edit the files here — changes are reflected everywhere.

## Screenshots

Referenced screenshots are in `docs/screenshots/`.

## Windows Note

Symlinks require Developer Mode or Administrator privileges on Windows.
If skills appear as small text files instead of markdown content, enable Developer Mode:

```
Settings > Update & Security > For developers > Developer Mode: ON
```

Then re-clone with: `git clone -c core.symlinks=true <url>`
