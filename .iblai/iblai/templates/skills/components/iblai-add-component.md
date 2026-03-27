# Add an IBL.ai SDK Component

A generic guide for adding any IBL.ai SDK component (`@iblai/iblai-js/web-containers`)
to a page. Use this when there is no dedicated skill for the specific component you need.

## Step 1: Discover the Component

Use the MCP tools to look up the component's props and usage:

```
// In Claude Code or Cursor with the IBL.ai MCP server active:
get_component_info("ComponentName")          // full props interface + usage
get_hook_info("useHookName")                 // hook parameters + return values
get_api_query_info("useGetSomethingQuery")   // RTK Query endpoint details
get_provider_setup("auth")                   // AuthProvider + TenantProvider hierarchy
get_integration_guide("chat")               // full integration guide for a feature
```

## Step 2: Choose the Import Path

| Import Path | When to Use |
|------------|-------------|
| `@iblai/iblai-js/web-containers` | Most components — framework-agnostic |
| `@iblai/iblai-js/web-containers/next` | Components that use `next/image` or `next/navigation` (e.g., `Account`, `SsoLogin`) |

## Step 3: Available Component Categories

### Profile & Account
```typescript
import {
  Profile,              // Full-page personal profile editor (7 tabs)
  UserProfileDropdown,  // Avatar dropdown (avatar, settings, logout)
  UserProfileModal,     // Modal combining Profile + Account
} from "@iblai/iblai-js/web-containers";

import {
  Account,             // Full-page org/account settings (Next.js required)
} from "@iblai/iblai-js/web-containers/next";
```

### Analytics
```typescript
import {
  AnalyticsLayout,           // Tab-based layout (Overview, Users, Topics, etc.)
  AnalyticsOverview,         // Overview dashboard
  AnalyticsUsersStats,       // User activity stats
  AnalyticsTopicsStats,      // Topic/conversation stats
  AnalyticsFinancialStats,   // Revenue / financial stats
  AnalyticsTranscriptsStats, // Transcript/message stats (needs next/navigation)
  AnalyticsReports,          // Downloadable data reports
  ChartFiltersProvider,      // Required context wrapper for all analytics
  StatCard,
  ChartCardWrapper,
  TimeFilter,
} from "@iblai/iblai-js/web-containers";
```

### Notifications
```typescript
import {
  NotificationDisplay,      // Full-page notification center (Inbox + Alerts)
  NotificationDropdown,     // Bell icon dropdown for navbar
  SendNotificationDialog,   // Dialog for composing/sending notifications
} from "@iblai/iblai-js/web-containers";
```

### Chat
```typescript
import {
  ConversationStarters,     // Clickable prompt buttons for chat
  SsoLogin,                 // SSO callback handler (needs next/navigation)
} from "@iblai/iblai-js/web-containers/next";
```

### Credentials & Catalog
```typescript
import {
  // Use get_component_info() to discover credential, catalog,
  // and course-related components
} from "@iblai/iblai-js/web-containers";
```

## Step 4: Page Boilerplate

Copy and adapt this template for any SDK component page:

```tsx
"use client";

import { useEffect, useState } from "react";
import { ComponentName } from "@iblai/iblai-js/web-containers";
import { config } from "@/lib/config";

function resolveTenantKey(raw: string | null): string {
  if (!raw || raw === "[object Object]") return "";
  try {
    const p = JSON.parse(raw);
    if (typeof p === "string") return p;
    if (p?.key) return p.key;
  } catch {}
  return raw;
}

export default function MyPage() {
  const [tenantKey, setTenantKey] = useState("");
  const [username, setUsername] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // username (user_nicename from SSO userData)
    try {
      const raw = localStorage.getItem("userData");
      if (raw) {
        const parsed = JSON.parse(raw);
        setUsername(parsed.user_nicename ?? parsed.username ?? "");
      }
    } catch {}

    // tenant key (resolve from JSON object or plain string)
    const stored =
      localStorage.getItem("current_tenant") ??
      localStorage.getItem("tenant");
    const resolved = resolveTenantKey(stored) || config.mainTenantKey();
    setTenantKey(resolved);

    // isAdmin (from tenants array — find current tenant's is_admin flag)
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

  if (!ready || !tenantKey) {
    return (
      <div
        style={{
          height: "100vh",
          width: "100vw",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>Loading…</p>
      </div>
    );
  }

  return (
    <div style={{ height: "100vh", width: "100vw", overflow: "auto" }}>
      <ComponentName
        tenant={tenantKey}
        username={username}
        isAdmin={isAdmin}
        onClose={() => {/* handle close */}}
        // ... add component-specific props from get_component_info()
      />
    </div>
  );
}
```

## Step 5: Common Prop Patterns

Most IBL.ai SDK components follow one of these prop patterns:

**Pattern A — User-scoped (profile, notifications)**
```typescript
{ org: tenantKey, userId: username, isAdmin }
```

**Pattern B — Tenant-scoped (account, analytics, management)**
```typescript
{ tenant: tenantKey, username, isAdmin }
```

**Pattern C — Mentor-scoped (chat, mentor settings)**
```typescript
{ tenantKey, mentorId, username }
```

Use `get_component_info("ComponentName")` to confirm which pattern a component uses.

## Step 6: Common Gotchas

### `initializeDataLayer` requires 5 args (data-layer v1.2+)
```typescript
// CORRECT — 5 args:
initializeDataLayer(dmUrl, lmsUrl, legacyLmsUrl, storageService, httpErrorHandler)

// WRONG — 4 args (breaks component data fetching):
initializeDataLayer(dmUrl, lmsUrl, storageService, httpErrorHandler)
```

### `@reduxjs/toolkit` must be deduplicated
The SDK and your app must share ONE copy of `@reduxjs/toolkit`. Without dedup,
RTK Query hooks inside SDK components can't find the Redux store (blank/empty data,
no HTTP requests). The `next.config.mjs` in generated apps handles this automatically.

### Components needing `TenantProvider`
Components that call `useTenantContext()` internally (e.g., `Account`/`OrganizationTab`,
some analytics components) require `TenantProvider` to be an ancestor. The base
providers template includes `TenantProvider` — ensure it is not removed.

### Components needing Next.js
Components in `@iblai/iblai-js/web-containers/next` use `next/image` or
`next/navigation`. Do not import them from the base `@iblai/iblai-js/web-containers`
path — they will fail to render or cause runtime errors.

### Dynamic `tenantKey` values
The `tenants` array in localStorage may store tenant objects as JSON rather than
plain strings. Always resolve through `resolveTenantKey()` (see boilerplate above).

## Specific Component Skills

For components with their own dedicated skills, use those instead:

| Component | Skill |
|-----------|-------|
| Profile (personal settings) | `/iblai-add-profile-page` |
| Account (org settings) | `/iblai-add-account-page` |
| Analytics dashboard | `/iblai-add-analytics-page` |
| Notifications | `/iblai-add-notifications-page` |
| Chat widget | `/iblai-add-chat` |
