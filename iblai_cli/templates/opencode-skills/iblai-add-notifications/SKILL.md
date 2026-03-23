---
name: iblai-add-notifications
description: Add IBL.ai Notifications
---

# Add IBL.ai Notifications

Add a notification bell with unread count badge and dropdown to this project.

## Prerequisites

- IBL.ai auth must already be integrated (run `/iblai-add-auth` first)

## Steps

### 1. Use MCP tools for documentation

- Call `get_component_info(componentName: "NotificationDropdown")` for the component API

### 2. Create the notification bell wrapper

Create `components/iblai/notification-bell.tsx` that:
- Uses `NotificationDropdown` from `@iblai/iblai-js/web-containers`
- Reads `tenant` and `userData` from localStorage for the `org` and `userId` props
- Optionally passes an `onViewNotifications` callback for "View all" navigation

### 3. Place in your navbar

```tsx
import { IblaiNotificationBell } from "@/components/iblai/notification-bell";

function Navbar() {
  return (
    <nav>
      {/* ... other nav items ... */}
      <IblaiNotificationBell onViewAll={() => router.push("/notifications")} />
    </nav>
  );
}
```

### 4. Verify

Run `pnpm dev`, log in, and check the bell icon shows with an unread count.
