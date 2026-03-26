# Add IBL.ai Chat Widget

Add a real-time AI chat widget powered by IBL.ai mentors to this project. The widget uses WebSocket streaming for live responses.

## Prerequisites

- IBL.ai auth must already be integrated (run `/iblai-add-auth` first)
- A mentor/agent ID from your IBL.ai platform

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
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.org
```

### 5. Use the widget

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";

<ChatWidget mentorId="your-mentor-id" />
```

The widget can be placed anywhere — in a page, in a sidebar, or in a modal/drawer for a floating chat experience.

### 6. Verify

Run `pnpm dev`, log in, and verify the chat connects and streams responses from the mentor.
