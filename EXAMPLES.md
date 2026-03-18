# IBL.ai CLI Examples

This document provides practical examples of using the IBL.ai CLI to create applications.

## Basic Usage

### Creating an Agent App

**Minimal command (interactive prompts):**

```bash
iblai startapp agent
```

This will prompt you for:
1. Platform key (tenant identifier)
2. Whether to add a mentor/agent ID
3. App name

**With platform key:**

```bash
iblai startapp agent --platform-key acme
```

**With both platform key and mentor ID:**

```bash
iblai startapp agent --platform-key acme --mentor-id my-agent-123
```

**Specify output directory:**

```bash
iblai startapp agent --platform-key acme --output ./my-apps
```

## Real-World Scenarios

### Scenario 1: Customer Support Agent

Create a customer support agent for "ACME Corp":

```bash
iblai startapp agent \
  --platform-key acme \
  --mentor-id customer-support \
  --output ./acme-support-agent
```

This generates an app that:
- Routes to `/platform/acme/customer-support`
- Connects to ACME's tenant
- Uses the customer-support agent configuration

### Scenario 2: Sales Assistant

Create a sales assistant without a specific agent ID:

```bash
iblai startapp agent \
  --platform-key mycompany \
  --output ./sales-assistant
```

Users can then configure the agent ID later in the environment variables.

### Scenario 3: Multi-Tenant Platform

Create an agent app for a multi-tenant platform:

```bash
iblai startapp agent \
  --platform-key main \
  --output ./platform-agent
```

Then customize the providers in `providers/index.tsx` to dynamically handle tenant switching.

## Post-Generation Steps

After generating an app:

### 1. Install Dependencies

```bash
cd my-agent-app
pnpm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` to set your actual environment variables:

```env
NEXT_PUBLIC_AUTH_URL=https://auth.yourcompany.com
NEXT_PUBLIC_DM_URL=https://api.yourcompany.com
NEXT_PUBLIC_BASE_WS_URL=wss://api.yourcompany.com
# ... etc
```

### 3. Run Development Server

```bash
pnpm dev
```

Visit `http://localhost:3000` to see your agent app.

### 4. Build for Production

```bash
pnpm build
pnpm start
```

## Customization

### Adding Custom Components

The generated app is just a starting point. You can customize it by:

1. **Adding new pages** in `app/platform/[tenantKey]/[agentId]/`:

```tsx
// app/platform/[tenantKey]/[agentId]/settings/page.tsx
export default function SettingsPage() {
  return <div>Settings</div>;
}
```

2. **Customizing the navbar** in `components/navbar.tsx`:

```tsx
// Add a new menu item
<DropdownMenuItem>
  <Cog className="mr-2 h-4 w-4" />
  Advanced Settings
</DropdownMenuItem>
```

3. **Extending the sidebar** in `components/app-sidebar.tsx`:

```tsx
// Add recent chats
<SidebarMenu>
  <SidebarMenuItem>
    <SidebarMenuButton>Recent Chats</SidebarMenuButton>
  </SidebarMenuItem>
</SidebarMenu>
```

4. **Customizing the chat** in `components/chat/`:

- Modify `welcome.tsx` to change the welcome screen
- Update `chat-messages.tsx` to customize message rendering
- Enhance `chat-input-form.tsx` to add file upload or voice input

### Using IBL.ai Packages

The generated app uses the `@iblai/iblai-js` unified SDK with subpath imports:

- `@iblai/iblai-js/data-layer` - For API calls and data management
- `@iblai/iblai-js/web-containers` - For UI components
- `@iblai/iblai-js/web-utils` - For hooks and utilities

**Example - Adding file upload:**

```tsx
import { useFileUpload } from "@iblai/iblai-js/web-utils";

function ChatInput() {
  const { uploadFile, isUploading } = useFileUpload();

  const handleFileSelect = async (file: File) => {
    await uploadFile(file);
  };

  // ... rest of component
}
```

**Example - Using data layer:**

```tsx
import { useGetMentorSettingsQuery } from "@iblai/iblai-js/data-layer";

function Settings() {
  const { data: settings, isLoading } = useGetMentorSettingsQuery({
    mentor: "my-agent",
    org: "acme",
  });

  // ... use settings
}
```

## Docker Deployment

The generated app is Docker-ready with runtime environment variables.

### 1. Build Docker Image

```dockerfile
FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Build the app
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# Production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

### 2. Runtime Environment Configuration

The `public/env.js` file allows environment variables to be injected at container startup:

```bash
# Start the container with environment variables
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_AUTH_URL=https://auth.prod.com \
  -e NEXT_PUBLIC_DM_URL=https://api.prod.com \
  my-agent-app
```

## Testing Your App

### Run Type Checking

```bash
pnpm typecheck
```

### Run Linting

```bash
pnpm lint
```

### Add Tests

Create a test file in `__tests__/`:

```typescript
// __tests__/chat.test.tsx
import { render, screen } from "@testing-library/react";
import { Chat } from "@/components/chat";

describe("Chat Component", () => {
  it("renders welcome screen", () => {
    render(<Chat />);
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
  });
});
```

## Troubleshooting

### Issue: "Module not found: @iblai/data-layer"

**Solution:** Make sure you've run `pnpm install` from the monorepo root to link workspace packages.

### Issue: "Cannot find module '@/components/ui/button'"

**Solution:** The app uses TypeScript path aliases. Make sure `tsconfig.json` includes the paths configuration.

### Issue: Authentication redirects not working

**Solution:** Check that `NEXT_PUBLIC_AUTH_URL` is set correctly in your `.env.local` file.

### Issue: WebSocket connection fails

**Solution:** Verify `NEXT_PUBLIC_BASE_WS_URL` points to your WebSocket server.

## Advanced Patterns

### Dynamic Tenant Switching

Modify `providers/index.tsx` to allow dynamic tenant switching:

```tsx
const [currentTenant, setCurrentTenant] = useState(config.mainTenantKey());

return (
  <TenantProvider
    currentTenant={currentTenant}
    onTenantChange={setCurrentTenant}
  >
    {children}
  </TenantProvider>
);
```

### Multi-Agent Support

Create a selector component to choose between multiple agents:

```tsx
// components/agent-selector.tsx
export function AgentSelector() {
  const agents = useAgents(); // Custom hook
  const router = useRouter();

  return (
    <Select onValueChange={(id) => router.push(`/platform/acme/${id}`)}>
      {agents.map((agent) => (
        <SelectItem key={agent.id} value={agent.id}>
          {agent.name}
        </SelectItem>
      ))}
    </Select>
  );
}
```

### Custom Authentication Flow

Override the `redirectToAuthSpa` function in `lib/utils.ts` for custom auth:

```typescript
export async function redirectToAuthSpa(
  redirectTo?: string,
  platformKey?: string,
  logout?: boolean
) {
  // Custom authentication logic
  if (logout) {
    await customLogout();
  } else {
    await customLogin(platformKey);
  }
}
```

## Getting Help

- **Documentation**: Check the [README.md](./README.md)
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.md)
- **Issues**: Report bugs on GitHub
- **Support**: Email support@ibl.ai
