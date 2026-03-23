---
name: iblai-startapp-agent
description: Scaffold an IBL.ai Agent Chat App
---

# Scaffold an IBL.ai Agent Chat App

Create a full-featured AI agent chat application with sidebar, navbar, and WebSocket streaming using the CLI.

## Steps

### 1. Run the CLI

```bash
uvx iblai-app-cli startapp agent --platform <your-tenant-key> --agent <mentor-unique-id>
# Or: npx @iblai/cli startapp agent --platform <your-tenant-key> --agent <mentor-unique-id>
```

### 2. Configure environment

```bash
cd <app-name>
cp .env.example .env.local
```

Edit `.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.org
NEXT_PUBLIC_AUTH_URL=https://auth.iblai.org
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.org
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.org
NEXT_PUBLIC_MAIN_TENANT_KEY=your-tenant
NEXT_PUBLIC_DEFAULT_AGENT_ID=your-mentor-unique-id
```

### 3. Install and run

```bash
pnpm install
pnpm dev
```

### 4. What you get

The agent app includes everything in the base app plus:

- **Full chat UI**: Sidebar with chat history, navbar with notifications and profile, chat input with file attachment
- **Agent routing**: `/platform/[tenantKey]/[agentId]` with dynamic routes
- **WebSocket streaming**: Real-time chat responses via `useAdvancedChat`
- **MentorProvider**: Mentor settings, session management, guided prompts
- **Markdown rendering**: AI responses rendered with `react-markdown`
- **12 Radix UI primitives**: Dialog, dropdown, tooltip, sidebar, etc.

### 5. Customize

- Change the mentor ID in `.env.local` (`NEXT_PUBLIC_DEFAULT_AGENT_ID`)
- Modify `components/chat/` for custom chat UI
- Edit `components/app-sidebar.tsx` for sidebar customization
- Edit `components/navbar.tsx` for navbar customization
