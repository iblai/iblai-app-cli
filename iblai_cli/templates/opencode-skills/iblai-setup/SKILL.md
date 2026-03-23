---
name: iblai-setup
description: Full IBL.ai Setup
---

# Full IBL.ai Setup

Set up a complete IBL.ai integration in this Next.js project: authentication, Redux store, providers, and optionally chat, profile, and notifications.

## Steps

### 1. Analyze the project

- Read `package.json` for existing dependencies
- Read `app/layout.tsx` for the current provider/layout structure
- Check for existing Redux store, auth setup, or IBL.ai integration

### 2. Install all dependencies

```bash
pnpm add @iblai/iblai-js @reduxjs/toolkit react-redux
```

### 3. Set up auth (required)

Follow the steps from `/iblai-add-auth`:
- Create `lib/iblai/config.ts`, `lib/iblai/storage-service.ts`, `lib/iblai/auth-utils.ts`
- Create `app/sso-login-complete/page.tsx`
- Create `store/iblai-store.ts`
- Create `providers/iblai-providers.tsx`
- Wrap root layout with `<IblaiProviders>`

### 4. Add environment variables

```
NEXT_PUBLIC_AUTH_URL=https://auth.iblai.org
NEXT_PUBLIC_DM_URL=https://base.manager.iblai.app
NEXT_PUBLIC_LMS_URL=https://learn.iblai.app
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.org
```

### 5. Add features (optional)

Ask the user which features they want:

- **Chat widget**: Follow `/iblai-add-chat` steps
- **Profile dropdown**: Follow `/iblai-add-profile` steps
- **Notifications**: Follow `/iblai-add-notifications` steps

### 6. Set up MCP + Claude skills

Create `.mcp.json`:
```json
{
  "mcpServers": {
    "iblai-js-mcp": {
      "command": "npx",
      "args": ["@iblai/mcp"]
    }
  }
}
```

This enables AI-assisted development with full SDK documentation available via MCP tools.

### 7. Verify

Run `pnpm dev` and confirm:
- Unauthenticated users are redirected to the Auth SPA
- After login, users return to the app with tokens stored
- Chat widget connects and streams (if added)
- Profile dropdown shows user info (if added)
- Notification bell shows unread count (if added)
