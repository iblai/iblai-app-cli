# ibl.ai App Setup Guide

Your app is already generated with ibl.ai authentication, providers, Redux
store, and pre-built components. Here's what you have and what you can do next.

---

## What's Already Set Up

### Authentication

- **AuthProvider** + **TenantProvider** wrap your app via `providers/index.tsx`
- **SSO callback** at `app/(auth)/sso-login-complete/page.tsx` — handles tokens after login
- Unauthenticated users are automatically redirected to `login.iblai.app`
- All tokens are stored in `localStorage` by the SSO callback

### Redux Store (`store/index.ts`)

```typescript
// Included by default:
coreApiSlice      // Core IBL API endpoints
mentorReducer     // Mentor/user/tenant API slices
mentorMiddleware  // RTK Query middleware for all slices
```

`@reduxjs/toolkit` is deduplicated via webpack aliases in `next.config.ts` to
prevent duplicate ReactReduxContext issues with SDK components.

### Pre-Generated Components (`components/iblai/`)

```typescript
import { ChatWidget } from "@/components/iblai/chat-widget";
// → Embeds the MentorAI platform in an iframe via <mentor-ai> web component

import { ProfileDropdown } from "@/components/iblai/profile-dropdown";
// → Avatar dropdown with profile link and logout

import { IblaiNotificationBell } from "@/components/iblai/notification-bell";
// → Bell icon with unread count badge
```

### `initializeDataLayer` (in `providers/index.tsx`)

Called synchronously with **5 args** (data-layer v1.2+ signature):

```typescript
initializeDataLayer(dmUrl, lmsUrl, legacyLmsUrl, storageService, httpErrorHandler)
```

This sets `Config.lmsUrl` and `Config.dmUrl` before any RTK Query hooks fire.

---

## Configure Your Environment

Edit `.env.local`:

```bash
# Consolidated API (recommended)
NEXT_PUBLIC_API_BASE_URL=https://api.iblai.app
NEXT_PUBLIC_AUTH_URL=https://login.iblai.app
NEXT_PUBLIC_BASE_WS_URL=wss://asgi.data.iblai.app
NEXT_PUBLIC_PLATFORM_BASE_DOMAIN=iblai.app
NEXT_PUBLIC_MAIN_TENANT_KEY=your-tenant
NEXT_PUBLIC_DEFAULT_AGENT_ID=your-mentor-id  # agent app only
```

---

## How Auth Data Is Stored in `localStorage`

| Key | Value | Set By |
|-----|-------|--------|
| `axd_token` | AXD access token | SSO callback |
| `axd_token_expires` | Expiry timestamp | SSO callback |
| `dm_token` | Data Manager token | SSO callback |
| `dm_token_expires` | Expiry timestamp | SSO callback |
| `edx_jwt_token` | LMS JWT token | SSO callback |
| `userData` | JSON: `{ user_nicename, email, ... }` | SSO callback |
| `tenant` | Current tenant key | SSO callback / TenantProvider |
| `current_tenant` | Tenant object JSON | TenantProvider |
| `tenants` | JSON array of all user tenants | TenantProvider |

### Standard Pattern for Reading Auth Data in a Page

```typescript
useEffect(() => {
  // username
  try {
    const raw = localStorage.getItem("userData");
    if (raw) setUsername(JSON.parse(raw).user_nicename ?? "");
  } catch {}

  // tenant key (handles both plain string and JSON object)
  const stored = localStorage.getItem("current_tenant") ?? localStorage.getItem("tenant");
  const resolved = resolveTenantKey(stored) || config.mainTenantKey();
  setTenantKey(resolved);

  // isAdmin — from the tenants array
  try {
    const tenantsRaw = localStorage.getItem("tenants");
    if (tenantsRaw) {
      const tenants = JSON.parse(tenantsRaw);
      const match = tenants.find((t: any) => t.key === resolved);
      if (match) setIsAdmin(!!match.is_admin);
    }
  } catch {}

  setReady(true);
}, []);
```

---

## Add New Pages

Use the dedicated skills to add full-page SDK components:

| Page | Skill | Component |
|------|-------|-----------|
| Personal profile editor | `/iblai-add-profile-page` | `Profile` |
| Organization settings | `/iblai-add-account-page` | `Account` |
| Analytics dashboard | `/iblai-add-analytics-page` | `AnalyticsOverview` |
| Notification center | `/iblai-add-notifications-page` | `NotificationDisplay` |
| Any other SDK component | `/iblai-add-component` | Any from `@iblai/iblai-js/web-containers` |

---

## Run E2E Tests

```bash
# Edit e2e/.env.development with your credentials first
pnpm test:e2e          # headless
pnpm test:e2e:ui       # interactive Playwright UI
pnpm test:e2e:headed   # headed browser mode
```

---

## Add UI Blocks (shadcnspace)

`components.json` is configured for shadcn/ui. Add production-ready UI blocks:

```bash
npx shadcn@latest add @shadcn-space/hero-01
npx shadcn@latest add @shadcn-space/dashboard-shell-01
```

Browse all blocks at https://shadcnspace.com/blocks

---

## MCP Server (AI-Assisted Development)

`.mcp.json` is included and points to `@iblai/mcp`. With Claude Code or Cursor,
you have access to MCP tools for SDK documentation:

```
get_component_info("Profile")         # full props interface
get_hook_info("useAdvancedChat")      # hook parameters
get_api_query_info("useGetUserMetadataQuery")  # API endpoint
get_provider_setup("auth")            # provider hierarchy
get_integration_guide("chat")         # integration guide
```
