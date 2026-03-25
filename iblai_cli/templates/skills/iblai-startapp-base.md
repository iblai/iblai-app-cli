# Scaffold an IBL.ai Base App

Create a new Next.js application with IBL.ai authentication and pre-built components using the CLI.

## Steps

### 1. Install the CLI

```bash
uvx iblai-app-cli startapp base --platform <your-tenant-key>
# Or: npx @iblai/cli startapp base --platform <your-tenant-key>
```

### 2. Configure environment

```bash
cd <app-name>
cp .env.example .env.local
```

Edit `.env.local` with your platform settings:

```
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.org
NEXT_PUBLIC_AUTH_URL=https://auth.iblai.org
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.org
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.org
NEXT_PUBLIC_MAIN_TENANT_KEY=your-tenant
```

### 3. Install dependencies and run

```bash
pnpm install
pnpm dev
```

### 4. What you get

The base app includes:

- **SSO Authentication**: Redirects to IBL Auth SPA, handles tokens via `/sso-login-complete`
- **Route groups**: `(app)/` for authenticated pages, `(auth)/` for SSO callback
- **Redux store**: `coreApiSlice` + `mentorReducer` for IBL API access
- **Pre-built components** (ready to import):
  - `@/components/iblai/chat-widget` — `<ChatWidget mentorId="..." />`
  - `@/components/iblai/profile-dropdown` — `<ProfileDropdown />`
  - `@/components/iblai/notification-bell` — `<IblaiNotificationBell />`
- **shadcn/ui support**: `components.json` configured, use `npx shadcn@latest add @shadcn-space/hero-01`
- **MCP server**: `.mcp.json` for AI-assisted development

### 5. Add components to a page

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";
import { ProfileDropdown } from "@/components/iblai/profile-dropdown";
import { IblaiNotificationBell } from "@/components/iblai/notification-bell";
```
