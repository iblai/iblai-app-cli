# Skills

AI assistant skills for Claude Code, OpenCode, and Cursor.
Invoke them with `/` in your AI assistant.

## Available Skills

| Skill | Description |
|-------|-------------|
| `/iblai-setup` | What's set up, env config, localStorage keys, MCP tools |
| `/iblai-add-auth` | Add SSO authentication to an existing project |
| `/iblai-add-chat` | Add real-time AI chat widget |
| `/iblai-add-profile` | Add profile dropdown to navbar |
| `/iblai-add-profile-page` | Full profile settings page (7 tabs) |
| `/iblai-add-account-page` | Organization/account settings page |
| `/iblai-add-analytics-page` | Analytics dashboard page |
| `/iblai-add-notifications` | Add notification bell to navbar |
| `/iblai-add-notifications-page` | Full notification center page |
| `/iblai-add-component` | Generic guide for any SDK component |
| `/iblai-add-test` | Playwright E2E test patterns |
| `/iblai-build-windows-msix` | Windows MSIX build for test and release |
| `/iblai-customize-chat` | ChatWidget props and customization |

## Screenshots

Referenced screenshots are in `docs/screenshots/`.

## Tool Integration

Skills are stored here in `skills/` and symlinked to tool-specific directories:

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
