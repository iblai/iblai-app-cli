# Add ibl.ai Chat

Add a real-time AI chat widget powered by ibl.ai mentors. The widget uses
the `<mentor-ai>` web component which handles WebSocket streaming, UI,
session management, and authentication automatically.

## Prerequisites

- ibl.ai auth must already be integrated (run `/iblai-add-auth` first)
- A mentor/agent ID from your ibl.ai platform

## Steps

### 1. Verify auth is set up

Check that `lib/iblai/config.ts`, `lib/iblai/auth-utils.ts`, `store/iblai-store.ts`, and `providers/iblai-providers.tsx` exist.

### 2. Use MCP tools for documentation

- Call `get_hook_info(hookName: "useAdvancedChat")` for the chat hook API
- Call `get_api_query_info(queryName: "useCreateSessionIdMutation")` for session management

### 3. Create the chat widget component

Create `components/iblai/chat-widget.tsx` that:
- Uses `useAdvancedChat` from `@iblai/iblai-js/web-utils`
- Connects via WebSocket to `${config.baseWsUrl()}/ws/langflow/`
- Renders messages, handles streaming state, and provides input
- Reads `axd_token`, `tenant`, and `userData` from localStorage

### 4. Add environment variable

Add to `.env.local`:
```
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.app
```

### 5. Use the widget

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";

<ChatWidget mentorId="your-mentor-id" />
```

The widget can be placed anywhere — in a page, in a sidebar, or in a modal/drawer for a floating chat experience.

### 6. Verify

Run `pnpm dev`, log in, and verify the chat connects and streams responses from the mentor.

---

## Customization

The ChatWidget wraps the `<mentor-ai>` Web Component from `@iblai/iblai-web-mentor`. It renders the MentorAI platform in an iframe and handles authentication automatically.

### Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `mentorId` | `string` | (required) | The mentor unique ID to chat with |
| `tenantKey` | `string` | from localStorage/config | Override the platform key |
| `mentorUrl` | `string` | `https://mentorai.{domain}` | Override the MentorAI platform URL |
| `theme` | `"light" \| "dark"` | `"light"` | Color theme |
| `width` | `number \| string` | `720` | Width in pixels (number) or CSS value (string) |
| `height` | `number \| string` | `600` | Height in pixels (number) or CSS value (string) |
| `className` | `string` | — | Additional CSS class for the outer container |

### Usage Examples

```tsx
// Basic
<ChatWidget mentorId="your-mentor-id" />

// Custom dimensions
<ChatWidget mentorId="..." width={900} height={700} />

// Full width
<ChatWidget mentorId="..." width="100%" />

// Responsive
<ChatWidget mentorId="..." width="min(720px, 100%)" height="calc(100vh - 64px)" />

// Dark theme
<ChatWidget mentorId="..." theme="dark" />

// Custom platform
<ChatWidget mentorId="..." tenantKey="my-org" />

// Override mentor URL
<ChatWidget mentorId="..." mentorUrl="https://custom-mentor.example.com" />
```

### How It Works

1. The component dynamically imports `@iblai/iblai-web-mentor` (client-only, SSR disabled)
2. It resolves the platform key from props → `localStorage.current_tenant` → `localStorage.tenant` → `config.mainTenantKey()`
3. It renders a `<mentor-ai>` custom element with `authrelyonhost` mode
4. The web component creates a Shadow DOM with an iframe to the MentorAI platform
5. All chat UI, WebSocket streaming, session management, and markdown rendering happen inside the iframe
