# Customize the IBL.ai ChatWidget

The ChatWidget wraps the `<mentor-ai>` Web Component from `@iblai/iblai-web-mentor`. It renders the MentorAI platform in an iframe and handles authentication automatically.

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `mentorId` | `string` | (required) | The mentor unique ID to chat with |
| `tenantKey` | `string` | from localStorage/config | Override the tenant/org key |
| `mentorUrl` | `string` | `https://mentorai.{domain}` | Override the MentorAI platform URL |
| `theme` | `"light" \| "dark"` | `"light"` | Color theme |
| `width` | `number \| string` | `720` | Width in pixels (number) or CSS value (string) |
| `height` | `number \| string` | `600` | Height in pixels (number) or CSS value (string) |
| `className` | `string` | — | Additional CSS class for the outer container |

## Usage Examples

### Basic usage

```tsx
import { ChatWidget } from "@/components/iblai/chat-widget";

<ChatWidget mentorId="your-mentor-id" />
```

### Custom dimensions

```tsx
// Fixed size
<ChatWidget mentorId="..." width={900} height={700} />

// Full width
<ChatWidget mentorId="..." width="100%" />

// Responsive
<ChatWidget mentorId="..." width="min(720px, 100%)" height="calc(100vh - 64px)" />
```

### Dark theme

```tsx
<ChatWidget mentorId="..." theme="dark" />
```

### Custom tenant

```tsx
<ChatWidget mentorId="..." tenantKey="my-org" />
```

### Override mentor URL

```tsx
<ChatWidget mentorId="..." mentorUrl="https://custom-mentor.example.com" />
```

## How It Works

1. The component dynamically imports `@iblai/iblai-web-mentor` (client-only, SSR disabled)
2. It resolves the tenant key from props → `localStorage.current_tenant` → `localStorage.tenant` → `config.mainTenantKey()`
3. It renders a `<mentor-ai>` custom element with `authrelyonhost` mode
4. The web component creates a Shadow DOM with an iframe to the MentorAI platform
5. All chat UI, WebSocket streaming, session management, and markdown rendering happen inside the iframe
